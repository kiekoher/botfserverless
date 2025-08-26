import logging
from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_current_user_id, get_supabase_adapter
from infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter()

logger = logging.getLogger(__name__)

# Note: The QR code and status endpoints have been removed as they were
# dependent on the old Redis-based architecture. The new gateway logs
# the QR code directly to the console for manual scanning.

@router.post("/agent/activate", tags=["Onboarding"])
async def activate_agent(
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    user_id: str = Depends(get_current_user_id),
):
    """Activate the agent associated with the current user."""
    try:
        agent = await supabase_adapter.get_agent_for_user(user_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_id = agent["id"]
        updated = await supabase_adapter.update_agent_status(agent_id, "active")
        if not updated:
            raise HTTPException(
                status_code=500, detail="Failed to update agent status"
            )

        return {"status": "ok", "agent_id": agent_id}
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - unexpected errors
        logger.error("Error activating agent: %s", e)
        raise HTTPException(
            status_code=500, detail="Internal server error while activating agent"
        )
