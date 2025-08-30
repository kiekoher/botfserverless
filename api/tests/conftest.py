import os
import time
import jwt
import pytest

# Set default environment variables for the test environment
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_ANON_KEY", "test_anon_key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "secret")
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("DEEPSEEK_API_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("FRONTEND_ORIGINS", "http://localhost")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

# New variables for the serverless architecture
os.environ.setdefault("CLOUDFLARE_ACCOUNT_ID", "test_account_id")
os.environ.setdefault("CLOUDFLARE_API_TOKEN", "test_api_token")
os.environ.setdefault("CLOUDFLARE_QUEUE_ID", "test_queue_id")

# Variables for Billing/Stripe
os.environ.setdefault("STRIPE_API_KEY", "sk_test_1234567890")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_1234567890")


@pytest.fixture(scope="module")
def client():
    """
    Yield a TestClient for a module.
    This client can be used to make requests to the FastAPI application.
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(auth_user_id="user-1"):
    """
    Creates a valid JWT token header for authentication.
    Allows specifying a user_id.
    """
    payload = {
        "sub": auth_user_id,
        "aud": "authenticated",
        "exp": time.time() + 3600
    }
    token = jwt.encode(payload, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
