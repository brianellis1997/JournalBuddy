from datetime import datetime, date
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel


GoalStatus = Literal["active", "completed", "paused", "abandoned"]
JournalingSchedule = Literal["morning", "evening", "both"]


class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None
    journaling_schedule: Optional[JournalingSchedule] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    target_date: Optional[date] = None
    journaling_schedule: Optional[JournalingSchedule] = None


class GoalResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    target_date: Optional[date]
    journaling_schedule: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
