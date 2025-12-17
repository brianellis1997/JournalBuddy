from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel


MoodType = Literal["great", "good", "okay", "bad", "terrible"]


class EntryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    mood: Optional[MoodType] = None


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[MoodType] = None


class EntryResponse(BaseModel):
    id: UUID
    title: Optional[str]
    content: str
    mood: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimilarEntryResponse(BaseModel):
    id: UUID
    title: Optional[str]
    content: str
    mood: Optional[str]
    created_at: datetime
    similarity: float


class EntryListResponse(BaseModel):
    entries: List[EntryResponse]
    total: int
    page: int
    limit: int
