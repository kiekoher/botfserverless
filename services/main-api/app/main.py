import os
import time
import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from redis.asyncio import Redis, from_url as redis_from_url
from redis.exceptions import ResponseError
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import jwt

# === Imports del proyecto ===
from app.core.use_cases.process_chat_message import ProcessChatMessage
from app.dependencies import (
    supabase_adapter,
    gemini_adapter,
    deepseek_v2_adapter,
    deepseek_chat_adapter,
    openai_embedding_adapter,
    ai_router,
)
from app.api.v1 import onboarding, agents, knowledge, quality, billing, reports
from app.core.config import get_settings

settings = get_settings()

# --------------------------
#   Configuración Redis
# --------------------------
REDIS_HOST = settings.redis_host
REDIS_PORT = settings.redis_port
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
STREAM_IN = "events:transcribed_message"
STREAM_OUT = "events:message_out"
CONSUMER_GROUP = "group:main-api"
CONSUMER_NAME = f"consumer:main-api-{os.getenv('HOSTNAME', '1')}"

DEAD_LETTER_QUEUE = "events:dead_letter_queue"
MAX_RETRIES = 3
RATE_LIMIT = settings.api_rate_limit

# --------------------------
#      FastAPI App
# --------------------------
_worker_stop_event: Optional[asyncio.Event] = None
_worker_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    global _worker_stop_event, _worker_task
    logger.info("🚀 FastAPI startup…")

    # Conectar a Redis
    app.state.redis = redis_from_url(REDIS_URL, decode_responses=True)
    logger.info("🔌 Redis client created.")

    # Lanzar worker
    _worker_stop_event = asyncio.Event()
    _worker_task = asyncio.create_task(main_loop(app.state.redis, _worker_stop_event))
    logger.info("✅ Worker background task scheduled.")

    yield

    logger.info("🛑 FastAPI shutdown…")

    # Detener worker
    if _worker_stop_event is not None:
        _worker_stop_event.set()
    if _worker_task is not None:
        try:
            await asyncio.wait_for(_worker_task, timeout=5)
        except asyncio.TimeoutError:
            _worker_task.cancel()
            with contextlib.suppress(Exception):
                await _worker_task
    logger.info("✅ Worker background task stopped.")

    # Cerrar conexión Redis
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        logger.info("🔌 Redis connection closed.")


app = FastAPI(title="Main API", version="1.0.0", lifespan=lifespan)

allowed_origins = [o.strip() for o in settings.frontend_origins.split(',') if o.strip()]
if not allowed_origins:
    raise RuntimeError('FRONTEND_ORIGINS environment variable must be set')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

Instrumentator().instrument(app).expose(app)



@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host
    user_key = 'anon'
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
            )
            user_key = payload.get('sub', user_key)
        except jwt.PyJWTError as exc:
            logger.warning("Invalid JWT in rate limit middleware: %s", exc)
    redis = request.app.state.redis
    key = f'rate_limit:{user_key}:{ip}'
    try:
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, 60)
        if current > RATE_LIMIT:
            return JSONResponse(status_code=429, content={'detail': 'Too Many Requests'})
    except Exception as e:
        logger.error('Rate limit middleware error: %s', e)
    return await call_next(request)


# --------------------------
#   Inicialización de deps
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🤖 Main API starting...")
logger.info("🔌 Using shared adapters from dependencies.")

# Store adapters in application state for reuse across endpoints
app.state.supabase_adapter = supabase_adapter
app.state.gemini_adapter = gemini_adapter
app.state.deepseek_v2_adapter = deepseek_v2_adapter
app.state.deepseek_chat_adapter = deepseek_chat_adapter
app.state.openai_embedding_adapter = openai_embedding_adapter
app.state.ai_router = ai_router

process_chat_message_use_case = ProcessChatMessage(
    router=ai_router, db_adapter=supabase_adapter
)


# --------------------------
#   Utilidades del worker
# --------------------------
async def ensure_consumer_group(redis_client: Redis):
    """
    Crea el consumer group si no existe de forma asíncrona.
    """
    try:
        await redis_client.ping()
    except Exception as e:
        logger.error("[ensure_consumer_group] Redis no disponible aún: %s", e)
        return False

    try:
        await redis_client.xgroup_create(
            STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True
        )
        logger.info("[ensure_consumer_group] Consumer group '%s' creado.", CONSUMER_GROUP)
    except ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info(
                "[ensure_consumer_group] Consumer group '%s' ya existe.", CONSUMER_GROUP
            )
        else:
            logger.error("[ensure_consumer_group] Error al crear grupo: %s", e)
            return False
    return True


async def process_message_with_retry(redis_client: Redis, message_id, message_data):
    """Procesa un mensaje con reintentos exponenciales."""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "Processing message %s, attempt %s/%s",
                message_id,
                attempt + 1,
                MAX_RETRIES,
            )
            user_id = message_data.get("userId")
            query = message_data.get("body")

            if not user_id or not query:
                logger.warning("Message missing userId or body, skipping.")
                return True  # reconocer y seguir

            bot_response_text = await process_chat_message_use_case.execute(
                user_id=user_id, user_query=query
            )

            output_payload = {"userId": user_id, "body": bot_response_text}
            await redis_client.xadd(STREAM_OUT, output_payload, maxlen=10000, approximate=True)
            logger.info("Published response for %s to %s", user_id, STREAM_OUT)
            return True

        except Exception as e:
            logger.error(
                "Error processing message %s on attempt %s: %s",
                message_id,
                attempt + 1,
                e,
            )
            if attempt + 1 == MAX_RETRIES:
                logger.error(
                    "Message %s failed after %s attempts. Moving to DLQ.",
                    message_id,
                    MAX_RETRIES,
                )
                return False
            await asyncio.sleep(2**attempt)  # backoff exponencial
    return False


async def main_loop(redis_client: Redis, stop_event: asyncio.Event):
    """Bucle principal del worker (no bloquea el arranque HTTP)."""
    logger.info("👂 Starting to listen for messages...")
    while not stop_event.is_set():
        if await ensure_consumer_group(redis_client):
            break
        logger.info("[worker] Reintentando creación de consumer group en 2s…")
        await asyncio.sleep(2)

    while not stop_event.is_set():
        try:
            response = await redis_client.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {STREAM_IN: ">"}, count=1, block=5000
            )
            if not response:
                continue

            for stream, messages in response:
                for message_id, message_data in messages:
                    logger.info("Received message %s: %s", message_id, message_data)
                    success = await process_message_with_retry(
                        redis_client, message_id, message_data
                    )

                    if success:
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        logger.info(
                            "Successfully processed and acknowledged message %s",
                            message_id,
                        )
                    else:
                        dlq_payload = message_data.copy()
                        dlq_payload["error_service"] = "main-api"
                        dlq_payload["error_timestamp"] = time.time()
                        await redis_client.xadd(DEAD_LETTER_QUEUE, dlq_payload, maxlen=10000, approximate=True)
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        logger.error(
                            "Moved message %s to DLQ '%s'",
                            message_id,
                            DEAD_LETTER_QUEUE,
                        )
        except Exception as e:
            logger.error("[worker] Critical error in main loop: %s", e)
            await asyncio.sleep(5)


# --------------------------
#   API Routers
# --------------------------
# Include the router in the main FastAPI app
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(quality.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

# --------------------------
# Ciclo de vida de la App manejado por "lifespan" en la creación de FastAPI.
# --------------------------
@app.get("/health")
async def health(request: Request):
    ok = False
    try:
        ok = await request.app.state.redis.ping()
    except Exception as e:
        logger.error("[health] Redis ping error: %s", e)
    return JSONResponse({"status": "ok", "redis": ok})


if __name__ == "__main__":
    # Ejecuta uvicorn al invocar: python -m app.main
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
