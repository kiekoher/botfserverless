from fastapi import HTTPException, Request
from app.infrastructure.supabase_adapter import SupabaseAdapter
from app.infrastructure.gemini_adapter import GeminiAdapter
from app.core.use_cases.process_chat_message import ProcessChatMessage

# Create singleton instances of our adapters
supabase_adapter = SupabaseAdapter()
gemini_adapter = GeminiAdapter()


def get_process_chat_message_use_case() -> ProcessChatMessage:
    """
    Dependency injector for the ProcessChatMessage use case.
    """
    return ProcessChatMessage(supabase_adapter, gemini_adapter)


def get_current_user_id(request: Request) -> str:
    """Extracts and validates the user ID from a Supabase JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1]
    try:
        user = supabase_adapter.client.auth.get_user(token)
        return user.user.id  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - depends on external service
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc
