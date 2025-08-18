from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    user_id: str
    query: str
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    response: str
    user_id: str
    context: Optional[List[str]] = None
