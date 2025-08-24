from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id, get_supabase_adapter
from app.infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter()


@router.get("/reports/opportunity-briefs", tags=["Reports"])
async def get_opportunity_briefs(
    user_id: str = Depends(get_current_user_id),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Return opportunity briefs."""
    return await adapter.get_opportunity_briefs(user_id)


@router.get("/reports/performance-log", tags=["Reports"])
async def get_performance_log(
    user_id: str = Depends(get_current_user_id),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Return performance logs."""
    return await adapter.get_performance_log(user_id)


@router.get("/reports/executive-summaries", tags=["Reports"])
async def get_executive_summaries(
    user_id: str = Depends(get_current_user_id),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Return executive summaries."""
    return await adapter.get_executive_summaries(user_id)
