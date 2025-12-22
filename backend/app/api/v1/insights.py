from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.insights import InsightsService

router = APIRouter()


@router.get("/summary")
async def get_insights_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete insights summary for the current user."""
    service = InsightsService(db)
    return await service.get_insights_summary(current_user.id)


@router.get("/mood-trends")
async def get_mood_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mood trends over time."""
    service = InsightsService(db)
    return await service.get_mood_trends(current_user.id, days=days)


@router.get("/patterns")
async def get_day_patterns(
    days: int = Query(90, ge=30, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get day-of-week patterns in mood."""
    service = InsightsService(db)
    return await service.get_day_of_week_patterns(current_user.id, days=days)


@router.get("/themes")
async def get_common_themes(
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(20, ge=5, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get common themes/topics from journal entries."""
    service = InsightsService(db)
    return await service.get_common_themes(current_user.id, days=days, limit=limit)


@router.get("/streak")
async def get_streak_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get journaling streak information."""
    service = InsightsService(db)
    return await service.get_streak_info(current_user.id)


@router.get("/journal-types")
async def get_journal_type_breakdown(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get breakdown by journal type (morning/evening/freeform)."""
    service = InsightsService(db)
    return await service.get_journal_type_breakdown(current_user.id, days=days)


@router.get("/goals")
async def get_goal_correlation(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get correlation between goals and mood."""
    service = InsightsService(db)
    return await service.get_goal_correlation(current_user.id, days=days)
