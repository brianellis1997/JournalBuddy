from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalCRUD:
    async def get_by_id(self, db: AsyncSession, goal_id: UUID, user_id: UUID) -> Optional[Goal]:
        result = await db.execute(
            select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> List[Goal]:
        query = select(Goal).where(Goal.user_id == user_id)

        if status:
            query = query.where(Goal.status == status)

        query = query.order_by(Goal.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, goal_in: GoalCreate, user_id: UUID) -> Goal:
        goal = Goal(
            user_id=user_id,
            title=goal_in.title,
            description=goal_in.description,
            target_date=goal_in.target_date,
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        return goal

    async def update(self, db: AsyncSession, goal: Goal, goal_in: GoalUpdate) -> Goal:
        update_data = goal_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
        await db.commit()
        await db.refresh(goal)
        return goal

    async def delete(self, db: AsyncSession, goal: Goal) -> None:
        await db.delete(goal)
        await db.commit()

    async def count_by_user(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count()).where(Goal.user_id == user_id)
        )
        return result.scalar() or 0

    async def count_by_status(self, db: AsyncSession, user_id: UUID, status: str) -> int:
        result = await db.execute(
            select(func.count()).where(
                Goal.user_id == user_id,
                Goal.status == status,
            )
        )
        return result.scalar() or 0


goal_crud = GoalCRUD()
