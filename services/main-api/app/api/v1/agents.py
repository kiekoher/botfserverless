from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.infrastructure.supabase_adapter import SupabaseAdapter
from app.dependencies import get_process_chat_message_use_case # Re-using for adapter access, can be cleaner

router = APIRouter()

# A real implementation would have a robust dependency to get user from JWT
# For now, we'll simulate it, but this is a CRITICAL security gap.
async def get_current_user_id_mock(request: Request) -> str:
    """
    Mock dependency to simulate getting a user ID.
    In a real app, this would come from a decoded JWT token.
    We are using a header for simulation purposes.
    """
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        # In a real app, you'd check for an Authorization header and raise 401
        raise HTTPException(status_code=401, detail="Missing user identification for mock auth")
    return user_id

class AgentConfig(BaseModel):
    name: str
    product_description: str
    base_prompt: str

@router.post("/agents/me", tags=["Agents"], status_code=201)
async def upsert_agent_for_current_user(
    config: AgentConfig,
    request: Request,
    user_id: str = Depends(get_current_user_id_mock)
):
    """
    Creates or updates the agent configuration for the currently authenticated user.
    """
    # This is not ideal, but it's a way to get the adapter instance
    # A better way would be to have a dependency for the adapter itself.
    supabase_adapter = request.app.state.supabase_adapter
    if not supabase_adapter:
         # Manually creating it if not on state
        supabase_adapter = SupabaseAdapter()

    try:
        agent = supabase_adapter.upsert_agent_config(
            user_id=user_id,
            name=config.name,
            product_description=config.product_description,
            base_prompt=config.base_prompt
        )
        if not agent:
            raise HTTPException(status_code=500, detail="Failed to save agent configuration.")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/me", tags=["Agents"])
async def get_agent_for_current_user(
    request: Request,
    user_id: str = Depends(get_current_user_id_mock)
):
    """
    Retrieves the agent configuration for the currently authenticated user.
    """
    supabase_adapter = request.app.state.supabase_adapter
    if not supabase_adapter:
        supabase_adapter = SupabaseAdapter()

    try:
        agent = supabase_adapter.get_agent_for_user(user_id=user_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent configuration not found for this user.")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
