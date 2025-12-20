from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage


class ChatCRUD:
    async def create_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_type: str = "voice",
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, session_type=session_type)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def add_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        role: str,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    async def add_messages_batch(
        self,
        db: AsyncSession,
        session_id: UUID,
        messages: List[dict],
    ) -> List[ChatMessage]:
        db_messages = []
        for msg in messages:
            message = ChatMessage(
                session_id=session_id,
                role=msg["role"],
                content=msg["content"],
            )
            db.add(message)
            db_messages.append(message)
        await db.commit()
        return db_messages

    async def get_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
    ) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_recent_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 10,
    ) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_today_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[ChatSession]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= today_start,
            )
            .order_by(desc(ChatSession.created_at))
        )
        return list(result.scalars().all())

    async def get_voice_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
    ) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.user_id == user_id,
                ChatSession.session_type == "voice",
            )
            .order_by(desc(ChatSession.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_session_summary(
        self,
        db: AsyncSession,
        session_id: UUID,
        summary: str,
        key_topics: str = "",
        goal_updates: str = "",
    ) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.summary = summary
            session.key_topics = key_topics
            session.goal_updates = goal_updates
            await db.commit()
            await db.refresh(session)
        return session


chat_crud = ChatCRUD()
