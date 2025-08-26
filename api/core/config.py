import os
from dataclasses import dataclass
from functools import lru_cache


import stripe


@dataclass
class Settings:
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str
    # AI Providers
    google_api_key: str
    deepseek_api_key: str
    openai_api_key: str
    # Frontend
    frontend_origins: str
    # Cloudflare
    cloudflare_account_id: str
    cloudflare_api_token: str
    cloudflare_queue_id: str
    # Stripe
    stripe_api_key: str
    stripe_webhook_secret: str
    frontend_url: str


@lru_cache
def get_settings() -> Settings:
    required = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_JWT_SECRET",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "FRONTEND_ORIGINS",
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_QUEUE_ID",
        "STRIPE_API_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "FRONTEND_URL",
    ]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    # Configure Stripe API key globally
    stripe.api_key = os.environ["STRIPE_API_KEY"]

    return Settings(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_anon_key=os.environ["SUPABASE_ANON_KEY"],
        supabase_jwt_secret=os.environ["SUPABASE_JWT_SECRET"],
        google_api_key=os.environ["GOOGLE_API_KEY"],
        deepseek_api_key=os.environ["DEEPSEEK_API_KEY"],
        openai_api_key=os.environ["OPENAI_API_KEY"],
        frontend_origins=os.environ["FRONTEND_ORIGINS"],
        cloudflare_account_id=os.environ["CLOUDFLARE_ACCOUNT_ID"],
        cloudflare_api_token=os.environ["CLOUDFLARE_API_TOKEN"],
        cloudflare_queue_id=os.environ["CLOUDFLARE_QUEUE_ID"],
        stripe_api_key=os.environ["STRIPE_API_KEY"],
        stripe_webhook_secret=os.environ["STRIPE_WEBHOOK_SECRET"],
        frontend_url=os.environ["FRONTEND_URL"],
    )
