from fastapi import APIRouter, Depends

from dependencies import get_current_user_id, get_supabase_adapter
from infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter()


@router.get("/billing/info", tags=["Billing"])
async def get_billing_info(
    user_id: str = Depends(get_current_user_id),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Return billing information for the authenticated user."""
    return await adapter.get_billing_info(user_id)
