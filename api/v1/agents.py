from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from infrastructure.supabase_adapter import SupabaseAdapter
from dependencies import get_current_user_id, get_supabase_adapter

router = APIRouter()

class AgentConfig(BaseModel):
    name: str
    product_description: str
    base_prompt: str


@router.get("/agents", tags=["Agents"])
async def list_agents_for_current_user(
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    user_id: str = Depends(get_current_user_id),
):
    """Return all agents for the authenticated user."""
    try:
        return await supabase_adapter.list_agents_for_user(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/me", tags=["Agents"], status_code=201)
async def upsert_agent_for_current_user(
    config: AgentConfig,
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    user_id: str = Depends(get_current_user_id),
):
    """
    Creates or updates the agent configuration for the currently authenticated user.
    """
    try:
        agent = await supabase_adapter.upsert_agent_config(
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
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    user_id: str = Depends(get_current_user_id),
):
    """
    Retrieves the agent configuration for the currently authenticated user.
    """
    try:
        agent = await supabase_adapter.get_agent_for_user(user_id=user_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent configuration not found for this user.")
        return agent
    except HTTPException:
        # Re-raise HTTPException directly to prevent it from being caught by the generic handler
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
