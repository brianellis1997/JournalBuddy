from typing import List
from uuid import UUID
from datetime import datetime, timedelta
import random
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.schemas.gamification import ScheduleStatus

logger = logging.getLogger(__name__)

MORNING_PROMPTS = [
    "Good morning! What are your intentions for today?",
    "Start your day with gratitude. What are you thankful for?",
    "What's the most important thing you want to accomplish today?",
    "How are you feeling as you start this new day?",
    "What would make today great?",
]

EVENING_PROMPTS = [
    "How did your day go? What went well?",
    "Reflect on today's experiences. What did you learn?",
    "What are you grateful for from today?",
    "What was the highlight of your day?",
    "How are you feeling as the day comes to a close?",
]


class ScheduleService:
    def get_random_prompt(self, journal_type: str) -> str:
        if journal_type == "morning":
            return random.choice(MORNING_PROMPTS)
        elif journal_type == "evening":
            return random.choice(EVENING_PROMPTS)
        return ""

    async def get_schedule_status(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_hour: int = None,
    ) -> ScheduleStatus:
        if current_hour is None:
            current_hour = datetime.utcnow().hour

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        result = await db.execute(
            select(Entry.journal_type)
            .where(
                Entry.user_id == user_id,
                Entry.created_at >= today_start,
                Entry.created_at < today_end,
                Entry.journal_type.in_(["morning", "evening"])
            )
        )
        completed_types = {row[0] for row in result.all()}

        morning_completed = "morning" in completed_types
        evening_completed = "evening" in completed_types

        should_show_morning = 5 <= current_hour < 12 and not morning_completed
        should_show_evening = 17 <= current_hour < 23 and not evening_completed

        morning_prompt = self.get_random_prompt("morning") if should_show_morning else None
        evening_prompt = self.get_random_prompt("evening") if should_show_evening else None

        return ScheduleStatus(
            morning_completed=morning_completed,
            evening_completed=evening_completed,
            morning_prompt=morning_prompt,
            evening_prompt=evening_prompt,
            should_show_morning=should_show_morning,
            should_show_evening=should_show_evening,
        )

    async def check_today_completion(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> tuple[bool, bool]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        result = await db.execute(
            select(Entry.journal_type)
            .where(
                Entry.user_id == user_id,
                Entry.created_at >= today_start,
                Entry.created_at < today_end,
                Entry.journal_type.in_(["morning", "evening"])
            )
        )
        completed_types = {row[0] for row in result.all()}

        return "morning" in completed_types, "evening" in completed_types


schedule_service = ScheduleService()
