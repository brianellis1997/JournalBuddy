from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta, date
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_groq import ChatGroq

from app.config import settings
from app.models.auto_summary import AutoSummary
from app.models.entry import Entry
from app.models.goal import Goal, GoalProgressUpdate
from app.schemas.auto_summary import AutoSummaryCreate

logger = logging.getLogger(__name__)


SUMMARY_PROMPT = """You are a thoughtful journaling companion analyzing a user's journal entries.

Analyze these journal entries from the past {period} and create a warm, personal reflection summary.

---
ENTRIES:
{entries}
---

{goals_section}

Generate a summary in this exact format:

TITLE: [A meaningful 3-6 word title that captures the essence of this period]

CONTENT: [Write 2-3 paragraphs reflecting on their week/month. Be warm and personal, like a friend summarizing what they heard. Reference specific things they mentioned - names, events, feelings. Notice patterns. Celebrate wins. Acknowledge challenges. End with an encouraging observation or insight.]

MOOD_TREND: [One of: improving, stable, declining, mixed]

KEY_THEMES: [3-5 comma-separated themes that emerged, e.g., "work stress, family time, fitness progress, creative projects"]

GOAL_PROGRESS: [Brief summary of any goal progress mentioned, or "No specific goal updates" if none]

Important:
- Be genuine and warm, not clinical
- Reference specific details from their entries
- Notice patterns they might not have seen
- Keep the content focused and meaningful"""


class AutoSummaryService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.7,
            max_tokens=1000,
        )

    async def get_summaries(
        self, db: AsyncSession, user_id: UUID, limit: int = 10
    ) -> List[AutoSummary]:
        result = await db.execute(
            select(AutoSummary)
            .where(AutoSummary.user_id == user_id)
            .order_by(AutoSummary.period_start.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_summary_by_id(
        self, db: AsyncSession, summary_id: UUID, user_id: UUID
    ) -> Optional[AutoSummary]:
        result = await db.execute(
            select(AutoSummary).where(
                AutoSummary.id == summary_id, AutoSummary.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_existing_summary(
        self, db: AsyncSession, user_id: UUID, period_type: str, period_start: date
    ) -> Optional[AutoSummary]:
        result = await db.execute(
            select(AutoSummary).where(
                AutoSummary.user_id == user_id,
                AutoSummary.period_type == period_type,
                AutoSummary.period_start == period_start,
            )
        )
        return result.scalar_one_or_none()

    def _get_period_dates(self, period_type: str) -> tuple[date, date]:
        today = date.today()
        if period_type == "weekly":
            start = today - timedelta(days=7)
            end = today - timedelta(days=1)
        else:
            start = today.replace(day=1) - timedelta(days=1)
            start = start.replace(day=1)
            end = today.replace(day=1) - timedelta(days=1)
        return start, end

    async def _get_entries_for_period(
        self, db: AsyncSession, user_id: UUID, start: date, end: date
    ) -> List[Entry]:
        result = await db.execute(
            select(Entry)
            .where(
                Entry.user_id == user_id,
                Entry.created_at >= datetime.combine(start, datetime.min.time()),
                Entry.created_at <= datetime.combine(end, datetime.max.time()),
            )
            .order_by(Entry.created_at)
        )
        return list(result.scalars().all())

    async def _get_goals(self, db: AsyncSession, user_id: UUID) -> List[Goal]:
        result = await db.execute(
            select(Goal).where(Goal.user_id == user_id, Goal.status == "active")
        )
        return list(result.scalars().all())

    def _format_entries_for_prompt(self, entries: List[Entry]) -> str:
        formatted = []
        for entry in entries:
            date_str = entry.created_at.strftime("%B %d, %Y")
            mood_str = f" (feeling {entry.mood})" if entry.mood else ""
            title_str = f" - {entry.title}" if entry.title else ""
            content = entry.content[:500] + "..." if len(entry.content) > 500 else entry.content
            formatted.append(f"[{date_str}{title_str}{mood_str}]\n{content}")
        return "\n\n".join(formatted)

    def _parse_llm_response(self, response: str) -> dict:
        result = {
            "title": "Weekly Reflection",
            "content": "",
            "mood_trend": "stable",
            "key_themes": "",
            "goal_progress": "",
        }

        current_key = None
        current_content = []

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("TITLE:"):
                if current_key and current_content:
                    result[current_key] = " ".join(current_content).strip()
                current_key = "title"
                current_content = [line.replace("TITLE:", "").strip()]
            elif line.startswith("CONTENT:"):
                if current_key and current_content:
                    result[current_key] = " ".join(current_content).strip()
                current_key = "content"
                current_content = [line.replace("CONTENT:", "").strip()]
            elif line.startswith("MOOD_TREND:"):
                if current_key and current_content:
                    result[current_key] = " ".join(current_content).strip()
                current_key = "mood_trend"
                current_content = [line.replace("MOOD_TREND:", "").strip().lower()]
            elif line.startswith("KEY_THEMES:"):
                if current_key and current_content:
                    result[current_key] = " ".join(current_content).strip()
                current_key = "key_themes"
                current_content = [line.replace("KEY_THEMES:", "").strip()]
            elif line.startswith("GOAL_PROGRESS:"):
                if current_key and current_content:
                    result[current_key] = " ".join(current_content).strip()
                current_key = "goal_progress"
                current_content = [line.replace("GOAL_PROGRESS:", "").strip()]
            elif current_key and line:
                current_content.append(line)

        if current_key and current_content:
            result[current_key] = " ".join(current_content).strip()

        valid_trends = ["improving", "stable", "declining", "mixed"]
        if result["mood_trend"] not in valid_trends:
            result["mood_trend"] = "stable"

        return result

    async def generate_summary(
        self, db: AsyncSession, user_id: UUID, period_type: str
    ) -> tuple[AutoSummary, bool]:
        period_start, period_end = self._get_period_dates(period_type)

        existing = await self.get_existing_summary(db, user_id, period_type, period_start)
        if existing:
            return existing, False

        entries = await self._get_entries_for_period(db, user_id, period_start, period_end)

        if not entries:
            raise ValueError(f"No entries found for the past {period_type} period")

        goals = await self._get_goals(db, user_id)
        goals_section = ""
        if goals:
            goals_text = "\n".join(f"- {g.title} ({g.progress}% complete)" for g in goals)
            goals_section = f"USER'S ACTIVE GOALS:\n{goals_text}\n---"

        entries_text = self._format_entries_for_prompt(entries)
        period_word = "week" if period_type == "weekly" else "month"

        prompt = SUMMARY_PROMPT.format(
            period=period_word,
            entries=entries_text,
            goals_section=goals_section,
        )

        try:
            response = await self.llm.ainvoke(prompt)
            parsed = self._parse_llm_response(response.content)
        except Exception as e:
            logger.error(f"LLM error generating summary: {e}")
            raise

        summary = AutoSummary(
            user_id=user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            title=parsed["title"],
            content=parsed["content"],
            mood_trend=parsed["mood_trend"],
            key_themes=parsed["key_themes"],
            goal_progress=parsed["goal_progress"],
            entry_count=len(entries),
        )

        db.add(summary)
        await db.commit()
        await db.refresh(summary)

        logger.info(f"Generated {period_type} summary for user {user_id}: {summary.id}")
        return summary, True


auto_summary_service = AutoSummaryService()
