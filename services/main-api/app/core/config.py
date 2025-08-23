import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    domain_name: str
    supabase_url: str
    supabase_key: str
    google_api_key: str
    deepseek_api_key: str
    openai_api_key: str
    redis_host: str
    redis_port: int
    frontend_origins: str
    api_rate_limit: int


@lru_cache
def get_settings() -> Settings:
    required = [
        "DOMAIN_NAME",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "FRONTEND_ORIGINS",
    ]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )
    return Settings(
        domain_name=os.environ["DOMAIN_NAME"],
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        google_api_key=os.environ["GOOGLE_API_KEY"],
        deepseek_api_key=os.environ["DEEPSEEK_API_KEY"],
        openai_api_key=os.environ["OPENAI_API_KEY"],
        redis_host=os.environ.get("REDIS_HOST", "redis"),
        redis_port=int(os.environ.get("REDIS_PORT", 6379)),
        frontend_origins=os.environ["FRONTEND_ORIGINS"],
        api_rate_limit=int(os.environ.get("API_RATE_LIMIT", 60)),
    )
