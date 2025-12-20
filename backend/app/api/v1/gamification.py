from typing import List
from datetime import datetime
from fastapi import APIRouter

from app.api.deps import Database, CurrentUser
from app.schemas.gamification import GamificationStats, AchievementResponse, ScheduleStatus, XPEventResponse
from app.services.gamification import gamification_service
from app.services.schedule import schedule_service

router = APIRouter()


@router.get("/stats", response_model=GamificationStats)
async def get_gamification_stats(
    current_user: CurrentUser,
    db: Database,
):
    stats = await gamification_service.get_gamification_stats(db, current_user.id)
    return stats


@router.get("/achievements", response_model=List[AchievementResponse])
async def get_achievements(
    current_user: CurrentUser,
    db: Database,
):
    achievements = await gamification_service.get_achievements(db, current_user.id)
    return achievements


@router.get("/schedule-status", response_model=ScheduleStatus)
async def get_schedule_status(
    current_user: CurrentUser,
    db: Database,
    hour: int = None,
):
    current_hour = hour if hour is not None else datetime.utcnow().hour
    status = await schedule_service.get_schedule_status(db, current_user.id, current_hour)
    return status


@router.get("/xp-history", response_model=List[XPEventResponse])
async def get_xp_history(
    current_user: CurrentUser,
    db: Database,
    limit: int = 20,
):
    from sqlalchemy import select
    from app.models.xp_event import XPEvent

    result = await db.execute(
        select(XPEvent)
        .where(XPEvent.user_id == current_user.id)
        .order_by(XPEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return [
        XPEventResponse(
            event_type=e.event_type,
            xp_amount=e.xp_amount,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.post("/check-achievements")
async def check_and_unlock_achievements(
    current_user: CurrentUser,
    db: Database,
):
    newly_unlocked = await gamification_service.check_achievements(db, current_user.id)
    return {"newly_unlocked": newly_unlocked}
