from datetime import datetime, timezone
from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel, field_serializer


MoodType = Literal["great", "good", "okay", "bad", "terrible"]
JournalType = Literal["morning", "evening", "freeform"]


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format with Z suffix for iOS compatibility."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


class EntryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    transcript: Optional[str] = None
    mood: Optional[MoodType] = None
    journal_type: Optional[JournalType] = None
    themes: Optional[List[str]] = None


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[MoodType] = None
    journal_type: Optional[JournalType] = None


class EntryResponse(BaseModel):
    id: UUID
    title: Optional[str]
    content: str
    transcript: Optional[str] = None
    mood: Optional[str]
    journal_type: Optional[str]
    themes: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at', 'updated_at')
    def serialize_dates(self, dt: datetime) -> str:
        return serialize_datetime(dt)


class SimilarEntryResponse(BaseModel):
    id: UUID
    title: Optional[str]
    content: str
    mood: Optional[str]
    created_at: datetime
    similarity: float

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return serialize_datetime(dt)


class EntryListResponse(BaseModel):
    entries: List[EntryResponse]
    total: int
    page: int
    limit: int
