from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id

router = APIRouter()


@router.get("/reports/opportunity-briefs", tags=["Reports"])
async def get_opportunity_briefs(user_id: str = Depends(get_current_user_id)):
    """Return placeholder opportunity briefs."""
    return {"user_id": user_id, "opportunities": []}


@router.get("/reports/performance-log", tags=["Reports"])
async def get_performance_log(user_id: str = Depends(get_current_user_id)):
    """Return placeholder performance logs."""
    return {"user_id": user_id, "logs": []}


@router.get("/reports/executive-summaries", tags=["Reports"])
async def get_executive_summaries(user_id: str = Depends(get_current_user_id)):
    """Return placeholder executive summaries."""
    return {"user_id": user_id, "summaries": []}
