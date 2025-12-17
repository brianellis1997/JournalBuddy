from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.api.deps import Database, CurrentUser
from app.crud.goal import goal_crud
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse

router = APIRouter()


@router.get("", response_model=List[GoalResponse])
async def list_goals(
    current_user: CurrentUser,
    db: Database,
    status_filter: Optional[str] = None,
):
    goals = await goal_crud.get_multi(db, current_user.id, status=status_filter)
    return goals


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_in: GoalCreate,
    current_user: CurrentUser,
    db: Database,
):
    goal = await goal_crud.create(db, goal_in, current_user.id)
    return goal


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    goal = await goal_crud.get_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    return goal


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    goal_in: GoalUpdate,
    current_user: CurrentUser,
    db: Database,
):
    goal = await goal_crud.get_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    goal = await goal_crud.update(db, goal, goal_in)
    return goal


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    goal = await goal_crud.get_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    await goal_crud.delete(db, goal)
    return {"success": True}
