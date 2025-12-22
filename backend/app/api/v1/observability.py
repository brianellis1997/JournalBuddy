from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.observability import ObservabilityService

router = APIRouter()


@router.get("/stats")
async def get_request_stats(
    hours: int = Query(24, ge=1, le=168),
    path_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated request statistics."""
    service = ObservabilityService(db)
    return await service.get_request_stats(hours=hours, path_filter=path_filter)


@router.get("/endpoints")
async def get_endpoint_breakdown(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get request counts and latency by endpoint."""
    service = ObservabilityService(db)
    return await service.get_endpoint_breakdown(hours=hours)


@router.get("/errors")
async def get_errors(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get error breakdown by type."""
    service = ObservabilityService(db)
    return await service.get_error_breakdown(hours=hours)


@router.get("/errors/recent")
async def get_recent_errors(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get most recent error logs."""
    service = ObservabilityService(db)
    return await service.get_recent_errors(limit=limit)


@router.get("/voice-sessions")
async def get_voice_session_stats(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get voice session performance statistics."""
    service = ObservabilityService(db)
    return await service.get_voice_session_stats(hours=hours)


@router.get("/latency-timeseries")
async def get_latency_timeseries(
    hours: int = Query(24, ge=1, le=168),
    bucket_minutes: int = Query(15, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """Get latency over time."""
    service = ObservabilityService(db)
    return await service.get_latency_timeseries(hours=hours, bucket_minutes=bucket_minutes)


@router.get("/llm")
async def get_llm_stats(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get LLM call statistics."""
    service = ObservabilityService(db)
    return await service.get_llm_stats(hours=hours)


@router.get("/tools")
async def get_tool_stats(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get tool call statistics by tool name."""
    service = ObservabilityService(db)
    return await service.get_tool_stats(hours=hours)


@router.get("/tools/recent")
async def get_recent_tool_calls(
    limit: int = Query(50, ge=1, le=200),
    tool_name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get recent tool calls."""
    service = ObservabilityService(db)
    return await service.get_recent_tool_calls(limit=limit, tool_name=tool_name)


@router.get("/tools/errors")
async def get_tool_errors(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get tool call errors."""
    service = ObservabilityService(db)
    return await service.get_tool_errors(hours=hours)


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get complete observability dashboard data."""
    service = ObservabilityService(db)
    return await service.get_dashboard_summary()
