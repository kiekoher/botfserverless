import os
import time
import asyncio
import contextlib
from contextlib import asynccontextmanager
from redis.asyncio import Redis, from_url as redis_from_url
from redis.exceptions import ResponseError
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# === Imports del proyecto ===
from app.core.use_cases.process_chat_message import ProcessChatMessage
from app.infrastructure.gemini_adapter import GeminiAdapter
from app.infrastructure.supabase_adapter import SupabaseAdapter
from app.core.ai_router import AIRouter
from app.infrastructure.deepseek_adapter import DeepSeekV2Adapter, DeepSeekChatAdapter
from app.infrastructure.openai_adapter import OpenAIEmbeddingAdapter

# --------------------------
#   Configuración Redis
# --------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
STREAM_IN = "events:transcribed_message"
STREAM_OUT = "events:message_out"
CONSUMER_GROUP = "group:main-api"
CONSUMER_NAME = "consumer:main-api-1"

DEAD_LETTER_QUEUE = "events:dead_letter_queue"
MAX_RETRIES = 3

# --------------------------
#      FastAPI App
# --------------------------
_worker_stop_event: Optional[asyncio.Event] = None
_worker_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    global _worker_stop_event, _worker_task
    print("🚀 FastAPI startup…")

    # Conectar a Redis
    app.state.redis = redis_from_url(REDIS_URL, decode_responses=True)
    print("🔌 Redis client created.")

    # Lanzar worker
    _worker_stop_event = asyncio.Event()
    _worker_task = asyncio.create_task(main_loop(app.state.redis, _worker_stop_event))
    print("✅ Worker background task scheduled.")

    yield

    print("🛑 FastAPI shutdown…")

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
    print("✅ Worker background task stopped.")

    # Cerrar conexión Redis
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        print("🔌 Redis connection closed.")


app = FastAPI(title="Main API", version="1.0.0", lifespan=lifespan)

# --------------------------
#   Inicialización de deps
# --------------------------
print("🤖 Main API starting...")

print("🔌 Initializing adapters...")
supabase_adapter = SupabaseAdapter()
gemini_adapter = GeminiAdapter()
deepseek_v2_adapter = DeepSeekV2Adapter(api_key=os.getenv("DEEPSEEK_API_KEY"))
deepseek_chat_adapter = DeepSeekChatAdapter(api_key=os.getenv("DEEPSEEK_API_KEY"))
openai_embedding_adapter = OpenAIEmbeddingAdapter(
    api_key=os.getenv("OPENAI_API_KEY"),
    supabase_adapter=supabase_adapter,
    gemini_adapter=gemini_adapter
)
print("✅ Adapters initialized.")

print("🧠 Initializing AI Router...")
ai_router = AIRouter(
    gemini_adapter=gemini_adapter,
    deepseek_v2_adapter=deepseek_v2_adapter,
    deepseek_chat_adapter=deepseek_chat_adapter,
    openai_embedding_adapter=openai_embedding_adapter,
)
print("✅ AI Router initialized.")

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
        print(f"[ensure_consumer_group] Redis no disponible aún: {e}")
        return False

    try:
        await redis_client.xgroup_create(
            STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True
        )
        print(f"[ensure_consumer_group] Consumer group '{CONSUMER_GROUP}' creado.")
    except ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(
                f"[ensure_consumer_group] Consumer group '{CONSUMER_GROUP}' ya existe."
            )
        else:
            print(f"[ensure_consumer_group] Error al crear grupo: {e}")
            return False
    return True


async def process_message_with_retry(redis_client: Redis, message_id, message_data):
    """Procesa un mensaje con reintentos exponenciales."""
    for attempt in range(MAX_RETRIES):
        try:
            print(
                f"Processing message {message_id}, attempt {attempt + 1}/{MAX_RETRIES}"
            )
            user_id = message_data.get("userId")
            query = message_data.get("body")

            if not user_id or not query:
                print("Message missing userId or body, skipping.")
                return True  # reconocer y seguir

            bot_response_text = await process_chat_message_use_case.execute(
                user_id=user_id, user_query=query
            )

            output_payload = {"userId": user_id, "body": bot_response_text}
            await redis_client.xadd(STREAM_OUT, output_payload)
            print(f"Published response for {user_id} to {STREAM_OUT}")
            return True

        except Exception as e:
            print(
                f"Error processing message {message_id} on attempt {attempt + 1}: {e}"
            )
            if attempt + 1 == MAX_RETRIES:
                print(
                    f"Message {message_id} failed after {MAX_RETRIES} attempts. Moving to DLQ."
                )
                return False
            await asyncio.sleep(2**attempt)  # backoff exponencial
    return False


async def main_loop(redis_client: Redis, stop_event: asyncio.Event):
    """Bucle principal del worker (no bloquea el arranque HTTP)."""
    print("👂 Starting to listen for messages...")
    while not stop_event.is_set():
        if await ensure_consumer_group(redis_client):
            break
        print("[worker] Reintentando creación de consumer group en 2s…")
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
                    print(f"Received message {message_id}: {message_data}")
                    success = await process_message_with_retry(
                        redis_client, message_id, message_data
                    )

                    if success:
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        print(
                            f"Successfully processed and acknowledged message {message_id}"
                        )
                    else:
                        dlq_payload = message_data.copy()
                        dlq_payload["error_service"] = "main-api"
                        dlq_payload["error_timestamp"] = time.time()
                        await redis_client.xadd(DEAD_LETTER_QUEUE, dlq_payload)
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        print(
                            f"Moved message {message_id} to DLQ '{DEAD_LETTER_QUEUE}'"
                        )
        except Exception as e:
            print(f"[worker] Critical error in main loop: {e}")
            await asyncio.sleep(5)


# --------------------------
# Ciclo de vida de la App manejado por "lifespan" en la creación de FastAPI.
# --------------------------
@app.get("/health")
async def health(request: Request):
    ok = False
    try:
        ok = await request.app.state.redis.ping()
    except Exception as e:
        print(f"[health] Redis ping error: {e}")
    return JSONResponse({"status": "ok", "redis": ok})


if __name__ == "__main__":
    # Ejecuta uvicorn al invocar: python -m app.main
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
