from fastapi import Depends, HTTPException, Request
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


def _get_token_payload(request: Request) -> dict:
    """
    Validates Supabase JWT and returns the payload.
    This is a private helper dependency.
    """
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

    return payload


def get_current_user_id(payload: dict = Depends(_get_token_payload)) -> str:
    """Extracts user ID from the token payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    return user_id


def require_admin_role(payload: dict = Depends(_get_token_payload)):
    """
    A dependency that requires the user to have an 'admin' role.
    Supabase roles are often in `app_metadata`. We check for a custom claim.
    """
    app_metadata = payload.get("app_metadata", {})
    # Using claims_admin is a common pattern for protected roles in Supabase
    is_admin = app_metadata.get("claims_admin", False)

    if not is_admin:
        raise HTTPException(status_code=403, detail="User is not authorized to perform this action")


def get_supabase_adapter() -> SupabaseAdapter:
    """Returns the shared Supabase adapter instance."""
    return supabase_adapter


async def check_message_quota(
    user_id: str = Depends(get_current_user_id),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """
    Dependency that checks if the user has enough message credits.
    Raises a 429 Too Many Requests error if credits are exhausted.
    """
    has_credits = await supabase.has_sufficient_credits(user_id)
    if not has_credits:
        raise HTTPException(
            status_code=429,
            detail="Message credit quota exhausted. Please upgrade your plan or wait for the next billing cycle.",
        )
