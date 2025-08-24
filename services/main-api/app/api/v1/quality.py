from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id, get_supabase_adapter
from app.infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter()


@router.get("/quality/metrics", tags=["Quality"])
async def get_quality_metrics(
    user_id: str = Depends(get_current_user_id),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Return quality metrics for the authenticated user."""
    return await adapter.get_quality_metrics(user_id)
