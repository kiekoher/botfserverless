import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.dependencies import get_current_user_id, get_supabase_adapter
from app.infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/onboarding/whatsapp-qr", tags=["Onboarding"])
async def get_whatsapp_qr(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Retrieves the WhatsApp QR code from Redis.
    The frontend should poll this endpoint until the QR code is available.
    """
    try:
        redis = request.app.state.redis
        qr_code = await redis.get(f"whatsapp:{user_id}:qr_code")
        if qr_code:
            return {"qr_code": qr_code}
        else:
            # It's normal for the QR code not to be present immediately.
            # Return a specific status code that the frontend can handle gracefully.
            return JSONResponse(status_code=204, content={"detail": "QR code not available yet."})
    except Exception as e:
        logger.error("Error getting QR code from Redis: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error while fetching QR code.")

@router.get("/onboarding/status", tags=["Onboarding"])
async def get_onboarding_status(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Retrieves the current WhatsApp connection status from Redis.
    """
    try:
        redis = request.app.state.redis
        status = await redis.get(f"whatsapp:{user_id}:status")
        return {"status": status or "disconnected"}
    except Exception as e:
        logger.error("Error getting status from Redis: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error while fetching status.")

# --- Activation Endpoint ---

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
