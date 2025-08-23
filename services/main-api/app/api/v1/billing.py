from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id

router = APIRouter()


@router.get("/billing/info", tags=["Billing"])
async def get_billing_info(user_id: str = Depends(get_current_user_id)):
    """Return placeholder billing information for the authenticated user."""
    # Real implementation would query billing provider or database
    return {
        "user_id": user_id,
        "plan": "trial",
        "credits_remaining": 0,
        "renewal_date": None,
    }
