from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.entry import Entry
from app.models.goal import Goal
from app.models.achievement import UserAchievement
from app.models.xp_event import XPEvent
from app.schemas.gamification import AchievementResponse, GamificationStats, XPEventResponse

logger = logging.getLogger(__name__)

XP_VALUES = {
    "entry_created": 10,
    "morning_journal": 15,
    "evening_journal": 15,
    "goal_created": 5,
    "goal_completed": 50,
    "streak_milestone_7": 100,
    "streak_milestone_30": 500,
    "streak_milestone_100": 1000,
    "achievement_unlocked": 25,
}

LEVEL_THRESHOLDS = [
    0,      # Level 1
    100,    # Level 2
    300,    # Level 3
    600,    # Level 4
    1000,   # Level 5
    1500,   # Level 6
    2100,   # Level 7
    2800,   # Level 8
    3600,   # Level 9
    4500,   # Level 10
    5500,   # Level 11
    6600,   # Level 12
    7800,   # Level 13
    9100,   # Level 14
    10500,  # Level 15
]

ACHIEVEMENTS = {
    "first_entry": {
        "name": "First Steps",
        "description": "Write your first journal entry",
        "icon": "pencil",
        "target": 1,
        "stat_key": "total_entries",
    },
    "entries_10": {
        "name": "Getting Started",
        "description": "Write 10 journal entries",
        "icon": "book",
        "target": 10,
        "stat_key": "total_entries",
    },
    "entries_50": {
        "name": "Dedicated Writer",
        "description": "Write 50 journal entries",
        "icon": "book-open",
        "target": 50,
        "stat_key": "total_entries",
    },
    "entries_100": {
        "name": "Century",
        "description": "Write 100 journal entries",
        "icon": "trophy",
        "target": 100,
        "stat_key": "total_entries",
    },
    "streak_7": {
        "name": "One Week Strong",
        "description": "Maintain a 7-day journaling streak",
        "icon": "flame",
        "target": 7,
        "stat_key": "longest_streak",
    },
    "streak_30": {
        "name": "Monthly Warrior",
        "description": "Maintain a 30-day journaling streak",
        "icon": "fire",
        "target": 30,
        "stat_key": "longest_streak",
    },
    "streak_100": {
        "name": "Unstoppable",
        "description": "Maintain a 100-day journaling streak",
        "icon": "medal",
        "target": 100,
        "stat_key": "longest_streak",
    },
    "first_goal": {
        "name": "Goal Setter",
        "description": "Create your first goal",
        "icon": "target",
        "target": 1,
        "stat_key": "total_goals",
    },
    "goals_completed_5": {
        "name": "Achiever",
        "description": "Complete 5 goals",
        "icon": "check-circle",
        "target": 5,
        "stat_key": "completed_goals",
    },
    "goals_completed_25": {
        "name": "Goal Master",
        "description": "Complete 25 goals",
        "icon": "star",
        "target": 25,
        "stat_key": "completed_goals",
    },
    "morning_routine": {
        "name": "Early Bird",
        "description": "Complete 7 morning journals",
        "icon": "sunrise",
        "target": 7,
        "stat_key": "morning_entries",
    },
    "evening_routine": {
        "name": "Night Owl",
        "description": "Complete 7 evening journals",
        "icon": "moon",
        "target": 7,
        "stat_key": "evening_entries",
    },
    "level_5": {
        "name": "Rising Star",
        "description": "Reach level 5",
        "icon": "star",
        "target": 5,
        "stat_key": "level",
    },
    "level_10": {
        "name": "Veteran Journaler",
        "description": "Reach level 10",
        "icon": "crown",
        "target": 10,
        "stat_key": "level",
    },
}


class GamificationService:
    def calculate_level(self, total_xp: int) -> Tuple[int, int, int]:
        level = 1
        for i, threshold in enumerate(LEVEL_THRESHOLDS):
            if total_xp >= threshold:
                level = i + 1
            else:
                break

        current_threshold = LEVEL_THRESHOLDS[level - 1] if level <= len(LEVEL_THRESHOLDS) else LEVEL_THRESHOLDS[-1]
        next_threshold = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else current_threshold + 1500

        xp_progress_in_level = total_xp - current_threshold
        xp_for_next_level = next_threshold - current_threshold

        return level, xp_for_next_level, xp_progress_in_level

    async def award_xp(
        self,
        db: AsyncSession,
        user_id: UUID,
        event_type: str,
        reference_id: Optional[UUID] = None,
    ) -> Tuple[int, bool]:
        xp_amount = XP_VALUES.get(event_type, 0)
        if xp_amount == 0:
            logger.warning(f"Unknown XP event type: {event_type}")
            return 0, False

        xp_event = XPEvent(
            user_id=user_id,
            event_type=event_type,
            xp_amount=xp_amount,
            reference_id=reference_id,
        )
        db.add(xp_event)

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return 0, False

        old_level = user.level
        user.total_xp += xp_amount
        new_level, _, _ = self.calculate_level(user.total_xp)
        user.level = new_level

        leveled_up = new_level > old_level

        await db.commit()
        logger.info(f"Awarded {xp_amount} XP to user {user_id} for {event_type}")

        return xp_amount, leveled_up

    async def get_user_stats(self, db: AsyncSession, user_id: UUID) -> dict:
        result = await db.execute(
            select(func.count(Entry.id)).where(Entry.user_id == user_id)
        )
        total_entries = result.scalar() or 0

        result = await db.execute(
            select(func.count(Entry.id)).where(
                Entry.user_id == user_id,
                Entry.journal_type == "morning"
            )
        )
        morning_entries = result.scalar() or 0

        result = await db.execute(
            select(func.count(Entry.id)).where(
                Entry.user_id == user_id,
                Entry.journal_type == "evening"
            )
        )
        evening_entries = result.scalar() or 0

        result = await db.execute(
            select(func.count(Goal.id)).where(Goal.user_id == user_id)
        )
        total_goals = result.scalar() or 0

        result = await db.execute(
            select(func.count(Goal.id)).where(
                Goal.user_id == user_id,
                Goal.status == "completed"
            )
        )
        completed_goals = result.scalar() or 0

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        level = user.level if user else 1

        current_streak, longest_streak = await self._calculate_streaks(db, user_id)

        return {
            "total_entries": total_entries,
            "morning_entries": morning_entries,
            "evening_entries": evening_entries,
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "level": level,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }

    async def _calculate_streaks(self, db: AsyncSession, user_id: UUID) -> Tuple[int, int]:
        result = await db.execute(
            select(func.date(Entry.created_at))
            .where(Entry.user_id == user_id)
            .distinct()
            .order_by(func.date(Entry.created_at).desc())
        )
        dates = [row[0] for row in result.all()]

        if not dates:
            return 0, 0

        today = datetime.utcnow().date()
        current_streak = 0
        longest_streak = 0
        streak = 0
        prev_date = None

        for i, entry_date in enumerate(dates):
            if i == 0:
                if entry_date == today or entry_date == today - timedelta(days=1):
                    streak = 1
                    current_streak = 1
                else:
                    streak = 1
                prev_date = entry_date
            else:
                if prev_date - entry_date == timedelta(days=1):
                    streak += 1
                    if i == 0 or (dates[0] == today or dates[0] == today - timedelta(days=1)):
                        current_streak = streak
                else:
                    longest_streak = max(longest_streak, streak)
                    streak = 1
                prev_date = entry_date

        longest_streak = max(longest_streak, streak)

        return current_streak, longest_streak

    async def check_achievements(self, db: AsyncSession, user_id: UUID) -> List[str]:
        stats = await self.get_user_stats(db, user_id)

        result = await db.execute(
            select(UserAchievement.achievement_key).where(UserAchievement.user_id == user_id)
        )
        unlocked_keys = {row[0] for row in result.all()}

        newly_unlocked = []

        for key, achievement in ACHIEVEMENTS.items():
            if key in unlocked_keys:
                continue

            stat_value = stats.get(achievement["stat_key"], 0)
            if stat_value >= achievement["target"]:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_key=key,
                )
                db.add(user_achievement)
                newly_unlocked.append(key)
                logger.info(f"User {user_id} unlocked achievement: {key}")

        if newly_unlocked:
            await db.commit()

        return newly_unlocked

    async def get_achievements(self, db: AsyncSession, user_id: UUID) -> List[AchievementResponse]:
        stats = await self.get_user_stats(db, user_id)

        result = await db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        unlocked = {ua.achievement_key: ua.unlocked_at for ua in result.scalars().all()}

        achievements = []
        for key, achievement in ACHIEVEMENTS.items():
            stat_value = stats.get(achievement["stat_key"], 0)
            achievements.append(AchievementResponse(
                key=key,
                name=achievement["name"],
                description=achievement["description"],
                icon=achievement["icon"],
                unlocked_at=unlocked.get(key),
                progress=min(stat_value, achievement["target"]),
                target=achievement["target"],
            ))

        return achievements

    async def get_gamification_stats(self, db: AsyncSession, user_id: UUID) -> GamificationStats:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        level, xp_for_next_level, xp_progress_in_level = self.calculate_level(user.total_xp)

        current_streak, longest_streak = await self._calculate_streaks(db, user_id)

        achievements = await self.get_achievements(db, user_id)

        result = await db.execute(
            select(XPEvent)
            .where(XPEvent.user_id == user_id)
            .order_by(XPEvent.created_at.desc())
            .limit(10)
        )
        recent_events = [
            XPEventResponse(
                event_type=e.event_type,
                xp_amount=e.xp_amount,
                created_at=e.created_at,
            )
            for e in result.scalars().all()
        ]

        return GamificationStats(
            total_xp=user.total_xp,
            level=level,
            xp_for_next_level=xp_for_next_level,
            xp_progress_in_level=xp_progress_in_level,
            current_streak=current_streak,
            longest_streak=longest_streak,
            achievements=achievements,
            recent_xp_events=recent_events,
        )


gamification_service = GamificationService()
