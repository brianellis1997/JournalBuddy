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
    created_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
