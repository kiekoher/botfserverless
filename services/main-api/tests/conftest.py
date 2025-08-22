import os

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "test")
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("DEEPSEEK_API_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

import app.main as app_main


async def _noop_main_loop(*args, **kwargs):
    return


app_main.main_loop = _noop_main_loop
