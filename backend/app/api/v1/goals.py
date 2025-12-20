from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import logging

from app.api.deps import Database, CurrentUser
from app.crud.goal import goal_crud
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse
from app.services.gamification import gamification_service
from app.core.database import async_session_maker

logger = logging.getLogger(__name__)
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
    background_tasks: BackgroundTasks,
):
    goal = await goal_crud.create(db, goal_in, current_user.id)
    background_tasks.add_task(award_goal_created_xp, current_user.id, goal.id)
    return goal


async def award_goal_created_xp(user_id: UUID, goal_id: UUID):
    try:
        async with async_session_maker() as db:
            await gamification_service.award_xp(db, user_id, "goal_created", goal_id)
            await gamification_service.check_achievements(db, user_id)
    except Exception as e:
        logger.error(f"Error awarding XP for goal creation: {e}")


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
    background_tasks: BackgroundTasks,
):
    goal = await goal_crud.get_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    old_status = goal.status
    goal = await goal_crud.update(db, goal, goal_in)

    if goal_in.status == "completed" and old_status != "completed":
        background_tasks.add_task(award_goal_completed_xp, current_user.id, goal.id)

    return goal


async def award_goal_completed_xp(user_id: UUID, goal_id: UUID):
    try:
        async with async_session_maker() as db:
            await gamification_service.award_xp(db, user_id, "goal_completed", goal_id)
            await gamification_service.check_achievements(db, user_id)
            logger.info(f"Awarded XP for completing goal {goal_id}")
    except Exception as e:
        logger.error(f"Error awarding XP for goal completion: {e}")


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
