from fastapi import HTTPException, Request
import time
import jwt
from jwt import InvalidTokenError

from core.ai_router import AIRouter
from infrastructure.deepseek_adapter import DeepSeekV2Adapter, DeepSeekChatAdapter
from infrastructure.gemini_adapter import GeminiAdapter
from infrastructure.openai_adapter import OpenAIEmbeddingAdapter
import httpx
from infrastructure.cloudflare_queue_adapter import CloudflareQueueAdapter
from infrastructure.supabase_adapter import SupabaseAdapter
from core.config import get_settings

settings = get_settings()

# Create singleton instances of our adapters
http_client = httpx.AsyncClient()
supabase_adapter = SupabaseAdapter()
cloudflare_queue_adapter = CloudflareQueueAdapter(
    account_id=settings.cloudflare_account_id,
    api_token=settings.cloudflare_api_token,
    queue_id=settings.cloudflare_queue_id,
    http_client=http_client,
)
gemini_adapter = GeminiAdapter(api_key=settings.google_api_key)
deepseek_v2_adapter = DeepSeekV2Adapter(api_key=settings.deepseek_api_key)
deepseek_chat_adapter = DeepSeekChatAdapter(api_key=settings.deepseek_api_key)
openai_embedding_adapter = OpenAIEmbeddingAdapter(
    api_key=settings.openai_api_key,
    supabase_adapter=supabase_adapter,
    gemini_adapter=gemini_adapter,
)

ai_router = AIRouter(
    gemini_adapter=gemini_adapter,
    deepseek_v2_adapter=deepseek_v2_adapter,
    deepseek_chat_adapter=deepseek_chat_adapter,
    openai_embedding_adapter=openai_embedding_adapter,
)


def get_current_user_id(request: Request) -> str:
    """Extracts and validates the user ID from a Supabase JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    exp = payload.get("exp")
    if exp and exp < time.time():
        raise HTTPException(status_code=401, detail="Token expired")
    aud = payload.get("aud")
    if aud and aud != "authenticated":
        raise HTTPException(status_code=401, detail="Invalid audience")

    try:
        user = supabase_adapter.client.auth.get_user(token)
        return user.user.id  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - depends on external service
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


def get_supabase_adapter() -> SupabaseAdapter:
    """Returns the shared Supabase adapter instance."""
    return supabase_adapter
