from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, field_serializer


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format with Z suffix for iOS compatibility."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


class AchievementResponse(BaseModel):
    key: str
    name: str
    description: str
    icon: str
    unlocked_at: Optional[datetime]
    progress: Optional[int]
    target: Optional[int]

    @field_serializer('unlocked_at')
    def serialize_unlocked_at(self, dt: Optional[datetime]) -> Optional[str]:
        return serialize_datetime(dt) if dt else None


class XPEventResponse(BaseModel):
    event_type: str
    xp_amount: int
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return serialize_datetime(dt)


class GamificationStats(BaseModel):
    total_xp: int
    level: int
    xp_for_next_level: int
    xp_progress_in_level: int
    current_streak: int
    longest_streak: int
    achievements: List[AchievementResponse]
    recent_xp_events: List[XPEventResponse]


class ScheduleStatus(BaseModel):
    morning_completed: bool
    evening_completed: bool
    morning_prompt: Optional[str]
    evening_prompt: Optional[str]
    should_show_morning: bool
    should_show_evening: bool


class NewAchievementNotification(BaseModel):
    achievement: AchievementResponse
    xp_earned: int


class LevelUpNotification(BaseModel):
    new_level: int
    xp_earned: int
