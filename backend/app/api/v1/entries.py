from typing import List, Optional
from uuid import UUID
import logging
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select

from app.api.deps import Database, CurrentUser
from app.crud.entry import entry_crud
from app.schemas.entry import EntryCreate, EntryUpdate, EntryResponse, EntryListResponse, SimilarEntryResponse
from app.services.embedding import embedding_service
from app.services.vector_search import search_similar_entries
from app.services.gamification import gamification_service
from app.core.database import async_session_maker
from app.models.entry import Entry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=EntryListResponse)
async def list_entries(
    current_user: CurrentUser,
    db: Database,
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
):
    skip = (page - 1) * limit
    entries, total = await entry_crud.get_multi(
        db, current_user.id, skip=skip, limit=limit, search=search
    )
    return EntryListResponse(
        entries=entries,
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry_in: EntryCreate,
    current_user: CurrentUser,
    db: Database,
    background_tasks: BackgroundTasks,
):
    entry = await entry_crud.create(db, entry_in, current_user.id)
    background_tasks.add_task(generate_entry_embedding, entry.id, entry.content)
    background_tasks.add_task(award_entry_xp, current_user.id, entry.id, entry_in.journal_type)
    return entry


async def award_entry_xp(user_id: UUID, entry_id: UUID, journal_type: Optional[str]):
    logger.info(f"Awarding XP for entry {entry_id}, type: {journal_type}")
    try:
        async with async_session_maker() as db:
            if journal_type == "morning":
                await gamification_service.award_xp(db, user_id, "morning_journal", entry_id)
            elif journal_type == "evening":
                await gamification_service.award_xp(db, user_id, "evening_journal", entry_id)
            else:
                await gamification_service.award_xp(db, user_id, "entry_created", entry_id)

            await gamification_service.check_achievements(db, user_id)
            logger.info(f"XP awarded for entry {entry_id}")
    except Exception as e:
        logger.error(f"Error awarding XP for entry {entry_id}: {e}")


async def generate_entry_embedding(entry_id: UUID, content: str):
    logger.info(f"Generating embedding for entry {entry_id}")
    try:
        embedding = await embedding_service.generate_embedding(content)
        logger.info(f"Generated embedding of length {len(embedding)} for entry {entry_id}")
        async with async_session_maker() as db:
            result = await db.execute(
                select(Entry).where(Entry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            if entry:
                entry.embedding = embedding
                await db.commit()
                logger.info(f"Saved embedding for entry {entry_id}")
            else:
                logger.warning(f"Entry {entry_id} not found when saving embedding")
    except Exception as e:
        logger.error(f"Error generating embedding for entry {entry_id}: {e}")


@router.get("/debug/embedding-status")
async def get_embedding_status(
    current_user: CurrentUser,
    db: Database,
):
    result = await db.execute(
        select(Entry.id, Entry.title, Entry.embedding).where(Entry.user_id == current_user.id)
    )
    entries = result.all()

    status_list = []
    for entry in entries:
        has_embedding = entry.embedding is not None
        embedding_length = len(entry.embedding) if has_embedding else 0
        status_list.append({
            "id": str(entry.id),
            "title": entry.title or "Untitled",
            "has_embedding": has_embedding,
            "embedding_length": embedding_length,
        })

    total = len(status_list)
    with_embeddings = sum(1 for s in status_list if s["has_embedding"])

    return {
        "total_entries": total,
        "entries_with_embeddings": with_embeddings,
        "entries_without_embeddings": total - with_embeddings,
        "entries": status_list,
    }


@router.post("/debug/regenerate-embeddings")
async def regenerate_all_embeddings(
    current_user: CurrentUser,
    db: Database,
):
    result = await db.execute(
        select(Entry).where(Entry.user_id == current_user.id)
    )
    entries = result.scalars().all()

    regenerated = 0
    errors = []

    for entry in entries:
        try:
            embedding = await embedding_service.generate_embedding(entry.content)
            entry.embedding = embedding
            regenerated += 1
            logger.info(f"Regenerated embedding for entry {entry.id}")
        except Exception as e:
            errors.append({"entry_id": str(entry.id), "error": str(e)})
            logger.error(f"Error regenerating embedding for entry {entry.id}: {e}")

    await db.commit()

    return {
        "total_entries": len(entries),
        "regenerated": regenerated,
        "errors": errors,
    }


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    entry = await entry_crud.get_by_id(db, entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )
    return entry


@router.patch("/{entry_id}", response_model=EntryResponse)
async def update_entry(
    entry_id: UUID,
    entry_in: EntryUpdate,
    current_user: CurrentUser,
    db: Database,
    background_tasks: BackgroundTasks,
):
    entry = await entry_crud.get_by_id(db, entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    entry = await entry_crud.update(db, entry, entry_in)

    if entry_in.content:
        background_tasks.add_task(generate_entry_embedding, entry.id, entry.content)

    return entry


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    entry = await entry_crud.get_by_id(db, entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )
    await entry_crud.delete(db, entry)
    return {"success": True}


@router.get("/{entry_id}/similar", response_model=List[SimilarEntryResponse])
async def get_similar_entries(
    entry_id: UUID,
    current_user: CurrentUser,
    db: Database,
    limit: int = 5,
):
    entry = await entry_crud.get_by_id(db, entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    if not entry.embedding:
        return []

    similar = await search_similar_entries(
        db, entry.embedding, str(current_user.id), limit=limit, exclude_id=str(entry_id)
    )
    return similar
