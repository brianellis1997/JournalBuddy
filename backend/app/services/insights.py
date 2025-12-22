import re
from datetime import datetime, timedelta
from uuid import UUID
from collections import Counter
from sqlalchemy import select, func, and_, extract, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.models.goal import Goal


MOOD_SCORES = {
    "terrible": 1,
    "bad": 2,
    "okay": 3,
    "good": 4,
    "great": 5,
}

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "d", "ll", "m", "o", "re", "ve", "y", "ain", "aren",
    "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn", "ma", "mightn",
    "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won", "wouldn",
    "today", "day", "really", "like", "think", "feel", "feeling", "felt",
    "going", "went", "got", "get", "getting", "thing", "things", "lot", "much",
    "make", "made", "said", "told", "know", "want", "need", "time", "way",
}


class InsightsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_mood_trends(self, user_id: UUID, days: int = 30) -> dict:
        """Get mood trends over time."""
        since = datetime.utcnow() - timedelta(days=days)

        date_col = func.date_trunc('day', Entry.created_at).label('date')
        result = await self.db.execute(
            select(
                date_col,
                Entry.mood,
                func.count(Entry.id).label('count'),
            )
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                    Entry.mood.isnot(None),
                )
            )
            .group_by(date_col, Entry.mood)
            .order_by(date_col)
        )

        daily_data = {}
        for row in result.fetchall():
            date_str = row.date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {"moods": {}, "avg_score": 0}
            daily_data[date_str]["moods"][row.mood] = row.count

        for date_str, data in daily_data.items():
            total_score = 0
            total_count = 0
            for mood, count in data["moods"].items():
                if mood in MOOD_SCORES:
                    total_score += MOOD_SCORES[mood] * count
                    total_count += count
            data["avg_score"] = round(total_score / total_count, 2) if total_count > 0 else 3.0

        timeline = [
            {"date": date, "avg_score": data["avg_score"], "moods": data["moods"]}
            for date, data in sorted(daily_data.items())
        ]

        mood_result = await self.db.execute(
            select(
                Entry.mood,
                func.count(Entry.id).label('count'),
            )
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                    Entry.mood.isnot(None),
                )
            )
            .group_by(Entry.mood)
        )

        mood_distribution = {row.mood: row.count for row in mood_result.fetchall()}
        total_entries = sum(mood_distribution.values())

        return {
            "period_days": days,
            "total_entries": total_entries,
            "mood_distribution": mood_distribution,
            "timeline": timeline,
            "average_mood_score": round(
                sum(MOOD_SCORES.get(m, 3) * c for m, c in mood_distribution.items()) / total_entries, 2
            ) if total_entries > 0 else None,
        }

    async def get_day_of_week_patterns(self, user_id: UUID, days: int = 90) -> dict:
        """Analyze patterns by day of week."""
        since = datetime.utcnow() - timedelta(days=days)

        dow_col = extract('dow', Entry.created_at).label('day_of_week')
        result = await self.db.execute(
            select(
                dow_col,
                Entry.mood,
                func.count(Entry.id).label('count'),
            )
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                    Entry.mood.isnot(None),
                )
            )
            .group_by(dow_col, Entry.mood)
        )

        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_data = {i: {"entries": 0, "mood_scores": [], "moods": {}} for i in range(7)}

        for row in result.fetchall():
            dow = int(row.day_of_week)
            day_data[dow]["entries"] += row.count
            day_data[dow]["moods"][row.mood] = row.count
            if row.mood in MOOD_SCORES:
                day_data[dow]["mood_scores"].extend([MOOD_SCORES[row.mood]] * row.count)

        patterns = []
        for dow, data in day_data.items():
            avg_score = round(sum(data["mood_scores"]) / len(data["mood_scores"]), 2) if data["mood_scores"] else None
            patterns.append({
                "day": day_names[dow],
                "day_number": dow,
                "entries": data["entries"],
                "avg_mood_score": avg_score,
                "moods": data["moods"],
            })

        best_day = max(patterns, key=lambda x: x["avg_mood_score"] or 0) if patterns else None
        worst_day = min(patterns, key=lambda x: x["avg_mood_score"] or 5) if patterns else None

        insights = []
        if best_day and best_day["avg_mood_score"]:
            insights.append(f"You tend to feel best on {best_day['day']}s (avg: {best_day['avg_mood_score']}/5)")
        if worst_day and worst_day["avg_mood_score"] and worst_day != best_day:
            insights.append(f"You tend to feel lowest on {worst_day['day']}s (avg: {worst_day['avg_mood_score']}/5)")

        return {
            "period_days": days,
            "patterns": patterns,
            "insights": insights,
            "best_day": best_day["day"] if best_day else None,
            "worst_day": worst_day["day"] if worst_day else None,
        }

    async def get_journal_type_breakdown(self, user_id: UUID, days: int = 30) -> dict:
        """Get breakdown by journal type."""
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                Entry.journal_type,
                func.count(Entry.id).label('count'),
                func.avg(
                    case(
                        (Entry.mood == 'terrible', 1),
                        (Entry.mood == 'bad', 2),
                        (Entry.mood == 'okay', 3),
                        (Entry.mood == 'good', 4),
                        (Entry.mood == 'great', 5),
                        else_=3,
                    )
                ).label('avg_mood'),
            )
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                )
            )
            .group_by(Entry.journal_type)
        )

        breakdown = [
            {
                "type": row.journal_type or "freeform",
                "count": row.count,
                "avg_mood_score": round(float(row.avg_mood), 2) if row.avg_mood else None,
            }
            for row in result.fetchall()
        ]

        return {
            "period_days": days,
            "breakdown": breakdown,
        }

    async def get_common_themes(self, user_id: UUID, days: int = 30, limit: int = 20) -> dict:
        """Extract common themes/topics from entries using stored LLM-extracted themes."""
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(Entry.themes)
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                    Entry.themes.isnot(None),
                )
            )
            .order_by(Entry.created_at.desc())
            .limit(100)
        )

        theme_counts = Counter()
        entries_with_themes = 0
        for row in result.fetchall():
            if row.themes:
                entries_with_themes += 1
                for theme in row.themes:
                    if theme and isinstance(theme, str):
                        theme_counts[theme.lower().strip()] += 1

        if entries_with_themes > 0:
            top_themes = theme_counts.most_common(limit)
            return {
                "period_days": days,
                "themes": [{"word": theme, "count": count} for theme, count in top_themes],
                "total_entries_analyzed": entries_with_themes,
                "source": "llm_extracted",
            }

        result = await self.db.execute(
            select(Entry.content, Entry.title)
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                )
            )
            .order_by(Entry.created_at.desc())
            .limit(100)
        )

        all_text = ""
        for row in result.fetchall():
            if row.title:
                all_text += " " + row.title
            if row.content:
                all_text += " " + row.content

        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        filtered_words = [w for w in words if w not in STOP_WORDS]
        word_counts = Counter(filtered_words)
        top_words = word_counts.most_common(limit)

        return {
            "period_days": days,
            "themes": [{"word": word, "count": count} for word, count in top_words],
            "total_words_analyzed": len(filtered_words),
            "source": "word_frequency",
        }

    async def get_streak_info(self, user_id: UUID) -> dict:
        """Get journaling streak information."""
        date_col = func.date_trunc('day', Entry.created_at).label('date')
        result = await self.db.execute(
            select(date_col)
            .where(Entry.user_id == user_id)
            .group_by(date_col)
            .order_by(date_col.desc())
        )

        dates = [row.date.date() for row in result.fetchall()]

        if not dates:
            return {"current_streak": 0, "longest_streak": 0, "total_days": 0}

        today = datetime.utcnow().date()
        current_streak = 0
        if dates and (dates[0] == today or dates[0] == today - timedelta(days=1)):
            current_streak = 1
            for i in range(1, len(dates)):
                if dates[i] == dates[i-1] - timedelta(days=1):
                    current_streak += 1
                else:
                    break

        longest_streak = 1
        current_run = 1
        for i in range(1, len(dates)):
            if dates[i] == dates[i-1] - timedelta(days=1):
                current_run += 1
                longest_streak = max(longest_streak, current_run)
            else:
                current_run = 1

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak if dates else 0,
            "total_days": len(dates),
            "first_entry_date": min(dates).isoformat() if dates else None,
        }

    async def get_goal_correlation(self, user_id: UUID, days: int = 30) -> dict:
        """Analyze correlation between goals and mood."""
        since = datetime.utcnow() - timedelta(days=days)

        goals_result = await self.db.execute(
            select(Goal)
            .where(Goal.user_id == user_id)
        )
        goals = goals_result.scalars().all()

        entries_result = await self.db.execute(
            select(Entry.content, Entry.mood, Entry.created_at)
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= since,
                    Entry.mood.isnot(None),
                )
            )
        )
        entries = entries_result.fetchall()

        goal_mentions = []
        for goal in goals:
            mentions = 0
            mood_when_mentioned = []
            goal_words = goal.title.lower().split()

            for entry in entries:
                content_lower = entry.content.lower()
                if any(word in content_lower for word in goal_words if len(word) > 3):
                    mentions += 1
                    if entry.mood in MOOD_SCORES:
                        mood_when_mentioned.append(MOOD_SCORES[entry.mood])

            avg_mood = round(sum(mood_when_mentioned) / len(mood_when_mentioned), 2) if mood_when_mentioned else None
            goal_mentions.append({
                "goal_id": str(goal.id),
                "goal_title": goal.title,
                "mentions": mentions,
                "avg_mood_when_mentioned": avg_mood,
                "goal_progress": goal.progress,
            })

        return {
            "period_days": days,
            "goals": sorted(goal_mentions, key=lambda x: x["mentions"], reverse=True),
        }

    async def get_insights_summary(self, user_id: UUID) -> dict:
        """Get a complete insights summary."""
        mood_trends = await self.get_mood_trends(user_id, days=30)
        day_patterns = await self.get_day_of_week_patterns(user_id, days=90)
        themes = await self.get_common_themes(user_id, days=30, limit=10)
        streak = await self.get_streak_info(user_id)
        journal_types = await self.get_journal_type_breakdown(user_id, days=30)

        return {
            "mood_trends": mood_trends,
            "day_patterns": day_patterns,
            "common_themes": themes,
            "streak": streak,
            "journal_types": journal_types,
        }
