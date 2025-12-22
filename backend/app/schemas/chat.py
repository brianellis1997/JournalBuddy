from datetime import datetime, timezone
from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel, field_serializer


RoleType = Literal["user", "assistant", "system"]


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format with Z suffix for iOS compatibility."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return serialize_datetime(dt)


class ChatSessionCreate(BaseModel):
    entry_id: Optional[UUID] = None


class ChatSessionResponse(BaseModel):
    id: UUID
    entry_id: Optional[UUID]
    session_type: str = "text"
    summary: Optional[str] = None
    key_topics: Optional[str] = None
    goal_updates: Optional[str] = None
    created_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return serialize_datetime(dt)


class VoiceSessionResponse(BaseModel):
    id: UUID
    session_type: str
    summary: Optional[str] = None
    key_topics: Optional[str] = None
    goal_updates: Optional[str] = None
    created_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return serialize_datetime(dt)
