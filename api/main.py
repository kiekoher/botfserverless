import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# === Imports del proyecto ===
from v1 import (
    onboarding,
    agents,
    knowledge,
    quality,
    billing,
    reports,
)
from core.config import get_settings
from dependencies import supabase_adapter, ai_router, cloudflare_queue_adapter

# --------------------------
#      Configuración
# --------------------------
settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
#      FastAPI App
# --------------------------
app = FastAPI(
    title="Main API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Configuración de CORS
allowed_origins = [o.strip() for o in settings.frontend_origins.split(",") if o.strip()]
if not allowed_origins:
    raise RuntimeError("FRONTEND_ORIGINS environment variable must be set")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
#   Inicialización de deps
# --------------------------
logger.info("🤖 Main API starting...")
# Store adapters in application state for reuse across endpoints
app.state.supabase_adapter = supabase_adapter
app.state.ai_router = ai_router

# Instanciar casos de uso
# La lógica de process_chat_message ya no se ejecuta directamente en la API.
# Se activará en los workers después de la transcripción y el embedding.
# process_chat_message_use_case = ProcessChatMessage(
#     router=ai_router, db_adapter=supabase_adapter
# )


# --------------------------
#   Endpoints de la API
# --------------------------
@app.post("/api/v1/messages/whatsapp")
async def handle_whatsapp_message(request: Request):
    """
    Este endpoint recibe los mensajes del gateway de WhatsApp,
    valida el payload y lo encola para el worker de transcripción.
    """
    message_payload = await request.json()
    logger.info(f"Received message from WhatsApp Gateway: {message_payload}")

    # Validación básica del payload
    user_id = message_payload.get("userId")
    if not user_id:
        logger.warning("Message payload missing 'userId'.")
        return JSONResponse(status_code=400, content={"detail": "Missing 'userId' in payload"})

    try:
        await cloudflare_queue_adapter.publish_message(message_payload)
    except Exception as e:
        logger.error(f"Failed to enqueue message for user {user_id}: {e}")
        return JSONResponse(status_code=500, content={"detail": "Failed to process message"})

    return JSONResponse(status_code=202, content={"status": "accepted"})


# --------------------------
#   API Routers
# --------------------------
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(quality.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


# --------------------------
#   Health Checks
# --------------------------
@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/health/deep")
async def deep_health(request: Request):
    """
    Performs a deep health check, verifying connectivity to the database.
    """
    db_ok = False
    errors = []
    try:
        # Executes a simple query to check DB connectivity.
        await request.app.state.supabase_adapter.client.rpc("is_rls_enabled").execute()
        db_ok = True
    except Exception as e:
        logger.error(f"[deep_health] Database connection error: {e}")
        errors.append(f"Database: {e}")

    if db_ok:
        return JSONResponse({"status": "healthy", "database": True})
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": False, "errors": errors},
        )
