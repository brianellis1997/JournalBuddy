from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.api.deps import Database, CurrentUser
from app.services.auto_summary import auto_summary_service
from app.schemas.auto_summary import (
    AutoSummaryResponse,
    AutoSummaryListResponse,
    GenerateSummaryResponse,
)

router = APIRouter()


@router.get("", response_model=AutoSummaryListResponse)
async def list_summaries(
    current_user: CurrentUser,
    db: Database,
    limit: int = 10,
):
    """List all auto-generated summaries for the current user."""
    summaries = await auto_summary_service.get_summaries(db, current_user.id, limit)
    return AutoSummaryListResponse(
        summaries=[AutoSummaryResponse.model_validate(s) for s in summaries],
        total=len(summaries),
    )


@router.get("/{summary_id}", response_model=AutoSummaryResponse)
async def get_summary(
    summary_id: UUID,
    current_user: CurrentUser,
    db: Database,
):
    """Get a specific summary by ID."""
    summary = await auto_summary_service.get_summary_by_id(db, summary_id, current_user.id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return AutoSummaryResponse.model_validate(summary)


@router.post("/generate/weekly", response_model=GenerateSummaryResponse)
async def generate_weekly_summary(
    current_user: CurrentUser,
    db: Database,
):
    """Generate a weekly summary from the past 7 days of journal entries."""
    try:
        summary, is_new = await auto_summary_service.generate_summary(db, current_user.id, "weekly")
        return GenerateSummaryResponse(
            summary=AutoSummaryResponse.model_validate(summary),
            is_new=is_new,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/generate/monthly", response_model=GenerateSummaryResponse)
async def generate_monthly_summary(
    current_user: CurrentUser,
    db: Database,
):
    """Generate a monthly summary from the past month of journal entries."""
    try:
        summary, is_new = await auto_summary_service.generate_summary(db, current_user.id, "monthly")
        return GenerateSummaryResponse(
            summary=AutoSummaryResponse.model_validate(summary),
            is_new=is_new,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )
