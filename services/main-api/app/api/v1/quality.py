from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id

router = APIRouter()


@router.get("/quality/metrics", tags=["Quality"])
async def get_quality_metrics(user_id: str = Depends(get_current_user_id)):
    """Return placeholder quality metrics for the authenticated user."""
    # In real implementation, fetch metrics from database or analytics service
    return {
        "user_id": user_id,
        "conversations_reviewed": 0,
        "avg_response_time_sec": 0,
        "csat": 0.0,
    }
