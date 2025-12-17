from fastapi import APIRouter

from app.api.deps import Database, CurrentUser
from app.crud.entry import entry_crud
from app.crud.goal import goal_crud
from app.schemas.metrics import MetricsResponse
from app.services.metrics import calculate_streak

router = APIRouter()


@router.get("", response_model=MetricsResponse)
async def get_metrics(current_user: CurrentUser, db: Database):
    total_entries = await entry_crud.count_by_user(db, current_user.id)
    entries_this_week = await entry_crud.count_this_week(db, current_user.id)
    entries_this_month = await entry_crud.count_this_month(db, current_user.id)

    entry_dates = await entry_crud.get_entry_dates(db, current_user.id)
    current_streak, longest_streak = calculate_streak(entry_dates)

    total_goals = await goal_crud.count_by_user(db, current_user.id)
    active_goals = await goal_crud.count_by_status(db, current_user.id, "active")
    completed_goals = await goal_crud.count_by_status(db, current_user.id, "completed")

    return MetricsResponse(
        total_entries=total_entries,
        current_streak=current_streak,
        longest_streak=longest_streak,
        entries_this_week=entries_this_week,
        entries_this_month=entries_this_month,
        total_goals=total_goals,
        active_goals=active_goals,
        completed_goals=completed_goals,
    )
