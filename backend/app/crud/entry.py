from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.schemas.entry import EntryCreate, EntryUpdate


class EntryCRUD:
    async def get_by_id(self, db: AsyncSession, entry_id: UUID, user_id: UUID) -> Optional[Entry]:
        result = await db.execute(
            select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
    ) -> tuple[List[Entry], int]:
        query = select(Entry).where(Entry.user_id == user_id)

        if search:
            query = query.where(Entry.content.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(desc(Entry.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        entries = result.scalars().all()

        return list(entries), total

    async def create(self, db: AsyncSession, entry_in: EntryCreate, user_id: UUID) -> Entry:
        entry = Entry(
            user_id=user_id,
            title=entry_in.title,
            content=entry_in.content,
            mood=entry_in.mood,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    async def update(self, db: AsyncSession, entry: Entry, entry_in: EntryUpdate) -> Entry:
        update_data = entry_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        await db.commit()
        await db.refresh(entry)
        return entry

    async def delete(self, db: AsyncSession, entry: Entry) -> None:
        await db.delete(entry)
        await db.commit()

    async def update_embedding(self, db: AsyncSession, entry: Entry, embedding: List[float]) -> Entry:
        entry.embedding = embedding
        await db.commit()
        await db.refresh(entry)
        return entry

    async def get_recent(
        self, db: AsyncSession, user_id: UUID, days: int = 7, limit: int = 10
    ) -> List[Entry]:
        since = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(Entry)
            .where(Entry.user_id == user_id, Entry.created_at >= since)
            .order_by(desc(Entry.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(Entry.id)).where(Entry.user_id == user_id)
        )
        return result.scalar() or 0

    async def count_this_week(self, db: AsyncSession, user_id: UUID) -> int:
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(func.count(Entry.id)).where(
                Entry.user_id == user_id,
                Entry.created_at >= week_ago,
            )
        )
        return result.scalar() or 0

    async def count_this_month(self, db: AsyncSession, user_id: UUID) -> int:
        month_ago = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(func.count(Entry.id)).where(
                Entry.user_id == user_id,
                Entry.created_at >= month_ago,
            )
        )
        return result.scalar() or 0

    async def get_entry_dates(self, db: AsyncSession, user_id: UUID) -> List[datetime]:
        result = await db.execute(
            select(Entry.created_at)
            .where(Entry.user_id == user_id)
            .order_by(desc(Entry.created_at))
        )
        return [row[0] for row in result.all()]


entry_crud = EntryCRUD()
