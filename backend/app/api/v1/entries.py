from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.api.deps import Database, CurrentUser
from app.crud.entry import entry_crud
from app.schemas.entry import EntryCreate, EntryUpdate, EntryResponse, EntryListResponse, SimilarEntryResponse
from app.services.embedding import embedding_service
from app.services.vector_search import search_similar_entries

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
    background_tasks.add_task(generate_entry_embedding, db, entry.id, entry.content)
    return entry


async def generate_entry_embedding(db, entry_id: UUID, content: str):
    try:
        embedding = await embedding_service.generate_embedding(content)
        entry = await entry_crud.get_by_id(db, entry_id, entry_id)
        if entry:
            await entry_crud.update_embedding(db, entry, embedding)
    except Exception:
        pass


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
        background_tasks.add_task(generate_entry_embedding, db, entry.id, entry.content)

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
