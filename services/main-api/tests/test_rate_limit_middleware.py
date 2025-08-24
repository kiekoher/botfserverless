import os
import sys
import types
import time
import jwt
import pytest
import pytest_asyncio
import httpx
import fakeredis.aioredis
from fastapi import FastAPI

# Stub modules required by app.dependencies
class Dummy:
    def __init__(self, *args, **kwargs):
        pass

sys.modules.setdefault("app.core.ai_router", types.SimpleNamespace(AIRouter=Dummy))
sys.modules.setdefault(
    "app.infrastructure.deepseek_adapter",
    types.SimpleNamespace(DeepSeekV2Adapter=Dummy, DeepSeekChatAdapter=Dummy),
)
sys.modules.setdefault(
    "app.infrastructure.gemini_adapter", types.SimpleNamespace(GeminiAdapter=Dummy)
)
sys.modules.setdefault(
    "app.infrastructure.openai_adapter",
    types.SimpleNamespace(OpenAIEmbeddingAdapter=Dummy),
)
sys.modules.setdefault(
    "app.infrastructure.supabase_adapter",
    types.SimpleNamespace(SupabaseAdapter=lambda: types.SimpleNamespace(client=types.SimpleNamespace(auth=types.SimpleNamespace(get_user=lambda token: types.SimpleNamespace(user=types.SimpleNamespace(id='user'))))))
)

os.environ.setdefault("DOMAIN_NAME", "example.com")
os.environ.setdefault("SUPABASE_URL", "http://example.com")
os.environ.setdefault("SUPABASE_KEY", "key")
os.environ.setdefault("GOOGLE_API_KEY", "key")
os.environ.setdefault("DEEPSEEK_API_KEY", "key")
os.environ.setdefault("OPENAI_API_KEY", "key")
os.environ.setdefault("FRONTEND_ORIGINS", "*")
os.environ.setdefault("SUPABASE_JWT_SECRET", "secret")

from app.main import rate_limit_middleware, app, settings  # noqa  E402

@pytest_asyncio.fixture()
async def client():
    test_app = FastAPI()
    test_app.middleware("http")(rate_limit_middleware)
    test_app.state.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    @test_app.get("/")
    async def index():
        return {"hello": "world"}

    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, test_app.state.redis

@pytest.mark.asyncio
async def test_valid_token(client):
    http_client, redis = client
    token = jwt.encode({"sub": "user1", "exp": time.time() + 60}, settings.supabase_jwt_secret, algorithm="HS256")
    resp = await http_client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert await redis.get("rate_limit:user1:127.0.0.1") == "1"

@pytest.mark.asyncio
async def test_invalid_token(client):
    http_client, redis = client
    bad_token = jwt.encode({"sub": "user2"}, "wrong", algorithm="HS256")
    resp = await http_client.get("/", headers={"Authorization": f"Bearer {bad_token}"})
    assert resp.status_code == 200
    assert await redis.get("rate_limit:anon:127.0.0.1") == "1"

@pytest.mark.asyncio
async def test_expired_token(client):
    http_client, redis = client
    expired = jwt.encode({"sub": "user3", "exp": time.time() - 10}, settings.supabase_jwt_secret, algorithm="HS256")
    resp = await http_client.get("/", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 200
    assert await redis.get("rate_limit:anon:127.0.0.1") == "1"
