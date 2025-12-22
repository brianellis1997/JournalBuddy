from typing import List, Optional
from uuid import UUID
import json
import logging

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import Database, CurrentUser
from app.models.chat import ChatSession, ChatMessage
from app.models.entry import Entry
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, ChatMessageResponse, VoiceSessionResponse
from app.agent.graph import journal_agent

router = APIRouter()


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    current_user: CurrentUser,
    db: Database,
    page: int = 1,
    limit: int = 20,
):
    skip = (page - 1) * limit
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    return sessions


@router.get("/voice-sessions", response_model=List[VoiceSessionResponse])
async def list_voice_sessions(
    current_user: CurrentUser,
    db: Database,
    limit: int = 20,
):
    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.user_id == current_user.id,
            ChatSession.session_type == "voice",
        )
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    if sessions:
        s = sessions[0]
        logger.info(f"voice-sessions: first session created_at={s.created_at}, tzinfo={s.created_at.tzinfo}")
        from app.schemas.chat import serialize_datetime
        logger.info(f"voice-sessions: serialized date = {serialize_datetime(s.created_at)}")

    return [
        VoiceSessionResponse(
            id=s.id,
            session_type=s.session_type,
            summary=s.summary,
            key_topics=s.key_topics,
            goal_updates=s.goal_updates,
            created_at=s.created_at,
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_in: ChatSessionCreate,
    current_user: CurrentUser,
    db: Database,
):
    session = ChatSession(
        user_id=current_user.id,
        entry_id=session_in.entry_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        entry_id=session.entry_id,
        created_at=session.created_at,
        messages=[],
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return session


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    await db.delete(session)
    await db.commit()
    return {"success": True}


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    message_in: ChatMessageCreate,
    current_user: CurrentUser,
    db: Database,
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_in.content,
    )
    db.add(user_message)
    await db.commit()

    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]

    entry_context = None
    if session.entry_id:
        entry_result = await db.execute(
            select(Entry).where(Entry.id == session.entry_id)
        )
        entry = entry_result.scalar_one_or_none()
        if entry:
            entry_context = {
                "title": entry.title,
                "content": entry.content,
                "mood": entry.mood,
                "created_at": entry.created_at.strftime("%B %d, %Y"),
            }

    async def generate():
        full_response = ""
        try:
            async for chunk in journal_agent.chat_stream(
                db,
                str(current_user.id),
                message_in.content,
                chat_history,
                entry_context=entry_context,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_message)
            await db.commit()

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/sessions/{session_id}/messages/sync", response_model=ChatMessageResponse)
async def send_message_sync(
    session_id: UUID,
    message_in: ChatMessageCreate,
    current_user: CurrentUser,
    db: Database,
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_in.content,
    )
    db.add(user_message)
    await db.commit()

    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]

    entry_context = None
    if session.entry_id:
        entry_result = await db.execute(
            select(Entry).where(Entry.id == session.entry_id)
        )
        entry = entry_result.scalar_one_or_none()
        if entry:
            entry_context = {
                "title": entry.title,
                "content": entry.content,
                "mood": entry.mood,
                "created_at": entry.created_at.strftime("%B %d, %Y"),
            }

    response_content = await journal_agent.chat(
        db,
        str(current_user.id),
        message_in.content,
        chat_history,
        entry_context=entry_context,
    )

    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response_content,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return assistant_message
