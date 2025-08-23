import os

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "test")
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("DEEPSEEK_API_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("R2_ENDPOINT_URL", "http://example.com")
os.environ.setdefault("R2_ACCESS_KEY_ID", "key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "secret")
os.environ.setdefault("R2_BUCKET_NAME", "bucket")
os.environ.setdefault("DOMAIN_NAME", "localhost")
os.environ.setdefault("FRONTEND_ORIGINS", "http://localhost")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")

import app.main as app_main


async def _noop_main_loop(*args, **kwargs):
    return


app_main.main_loop = _noop_main_loop
