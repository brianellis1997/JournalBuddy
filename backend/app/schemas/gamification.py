from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AchievementResponse(BaseModel):
    key: str
    name: str
    description: str
    icon: str
    unlocked_at: Optional[datetime]
    progress: Optional[int]
    target: Optional[int]


class XPEventResponse(BaseModel):
    event_type: str
    xp_amount: int
    created_at: datetime

    class Config:
        from_attributes = True


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
