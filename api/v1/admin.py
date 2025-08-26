from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, UUID4
import datetime

from dependencies import require_admin_role, get_supabase_adapter
from infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_role)]
)

# --- Pydantic Models for Admin Panel Responses ---

class AdminAgent(BaseModel):
    """Represents an agent for the admin panel."""
    id: UUID4
    name: str
    model: Optional[str] = None
    created_at: datetime.datetime
    config: Optional[dict] = None

class AdminConversation(BaseModel):
    """Represents a conversation for the admin panel."""
    id: UUID4
    user_id: UUID4
    agent_id: UUID4
    created_at: datetime.datetime
    ended_at: Optional[datetime.datetime] = None


# --- Admin Endpoints ---

@router.get("/agents", response_model=List[AdminAgent], summary="List all agents")
async def list_agents(
    supabase: SupabaseAdapter = Depends(get_supabase_adapter)
):
    """
    Retrieves a list of all agents in the system.
    This is a protected endpoint and requires admin privileges.
    """
    try:
        response = await supabase.client.from_("agents").select("id, name, model, created_at, config").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        # Log the exception here if logging is set up
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching agents: {str(e)}")

@router.get("/conversations", response_model=List[AdminConversation], summary="List recent conversations")
async def list_conversations(
    limit: int = 100,
    supabase: SupabaseAdapter = Depends(get_supabase_adapter)
):
    """
    Retrieves a list of the most recent conversations.
    This is a protected endpoint and requires admin privileges.
    """
    try:
        response = await supabase.client.from_("conversations").select("id, user_id, agent_id, created_at, ended_at").order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        # Log the exception here
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching conversations: {str(e)}")
