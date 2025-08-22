from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.infrastructure.supabase_adapter import SupabaseAdapter
from app.dependencies import get_current_user_id

router = APIRouter()

class AgentConfig(BaseModel):
    name: str
    product_description: str
    base_prompt: str

@router.post("/agents/me", tags=["Agents"], status_code=201)
async def upsert_agent_for_current_user(
    config: AgentConfig,
    request: Request,
    user_id: str = Depends(get_current_user_id)
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
    user_id: str = Depends(get_current_user_id)
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
