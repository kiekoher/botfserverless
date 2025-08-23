import asyncio
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.dependencies import get_current_user_id

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
        qr_code = await redis.get("whatsapp:qr_code")
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
        status = await redis.get("whatsapp:status")
        return {"status": status or "disconnected"}
    except Exception as e:
        logger.error("Error getting status from Redis: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error while fetching status.")

# --- Mock Endpoints for Frontend Development ---

@router.post("/agent/activate", tags=["Onboarding"])
async def mock_activate_agent():
    """
    Mock endpoint for activating the agent.
    """
    await asyncio.sleep(0.5)
    return {"status": "ok", "message": "Agent activated successfully (mocked)."}
