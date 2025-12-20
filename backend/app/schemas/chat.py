from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel


RoleType = Literal["user", "assistant", "system"]


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


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
