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
    admin,
)
from core.config import get_settings
from dependencies import supabase_adapter, ai_router, cloudflare_queue_adapter

# --------------------------
#      Configuración
# --------------------------
import os
from logtail import LogtailHandler

settings = get_settings()

# --- Logging Configuration ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []  # Evita duplicados si el módulo se recarga

# Handler para la consola (logs de Vercel, desarrollo local)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Handler para BetterStack (si el token está configurado)
BETTERSTACK_SOURCE_TOKEN = os.getenv("BETTERSTACK_SOURCE_TOKEN")
if BETTERSTACK_SOURCE_TOKEN:
    try:
        logtail_handler = LogtailHandler(source_token=BETTERSTACK_SOURCE_TOKEN)
        logtail_handler.setLevel(logging.INFO)
        logger.addHandler(logtail_handler)
        logger.info("BetterStack log handler configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure BetterStack handler: {e}")
else:
    logger.info("BETTERSTACK_SOURCE_TOKEN not found. Logging to console only.")
# --- End Logging Configuration ---


# --------------------------
#      FastAPI App
# --------------------------
app = FastAPI(
    title="Main API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Middleware para añadir Headers de Seguridad
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # Podríamos añadir un Content-Security-Policy aquí en el futuro si es necesario.
    # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    return response

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
# app.include_router(billing.router, prefix="/api/v1") # Disabled for Beta
# app.include_router(reports.router, prefix="/api/v1") # Disabled for Beta
app.include_router(admin.router, prefix="/api/v1")


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
