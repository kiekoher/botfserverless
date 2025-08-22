import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/onboarding/whatsapp-qr", tags=["Onboarding"])
async def get_whatsapp_qr(request: Request):
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
        print(f"Error getting QR code from Redis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching QR code.")

@router.get("/onboarding/status", tags=["Onboarding"])
async def get_onboarding_status(request: Request):
    """
    Retrieves the current WhatsApp connection status from Redis.
    """
    try:
        redis = request.app.state.redis
        status = await redis.get("whatsapp:status")
        return {"status": status or "disconnected"}
    except Exception as e:
        print(f"Error getting status from Redis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching status.")

# --- Mock Endpoints for Frontend Development ---

@router.post("/agent/activate", tags=["Onboarding"])
async def mock_activate_agent():
    """
    Mock endpoint for activating the agent.
    """
    await asyncio.sleep(0.5)
    return {"status": "ok", "message": "Agent activated successfully (mocked)."}
