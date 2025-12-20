from datetime import datetime, date
from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel


PeriodType = Literal["weekly", "monthly"]
MoodTrend = Literal["improving", "stable", "declining", "mixed"]


class AutoSummaryCreate(BaseModel):
    period_type: PeriodType
    period_start: date
    period_end: date
    title: str
    content: str
    mood_trend: Optional[MoodTrend] = None
    key_themes: Optional[str] = None
    goal_progress: Optional[str] = None
    entry_count: int = 0


class AutoSummaryResponse(BaseModel):
    id: UUID
    period_type: str
    period_start: date
    period_end: date
    title: str
    content: str
    mood_trend: Optional[str]
    key_themes: Optional[str]
    goal_progress: Optional[str]
    entry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AutoSummaryListResponse(BaseModel):
    summaries: List[AutoSummaryResponse]
    total: int


class GenerateSummaryRequest(BaseModel):
    period_type: PeriodType


class GenerateSummaryResponse(BaseModel):
    summary: AutoSummaryResponse
    is_new: bool
