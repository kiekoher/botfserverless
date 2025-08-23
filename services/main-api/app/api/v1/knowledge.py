import os
import uuid
import logging

import boto3
from botocore.client import Config
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request

from app.dependencies import get_current_user_id, get_supabase_adapter
from app.infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter()

logger = logging.getLogger(__name__)

def load_r2_config() -> dict[str, str]:
    required_keys = [
        "R2_ENDPOINT_URL",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
    ]
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            f"Missing R2 configuration variables: {', '.join(missing)}"
        )
    return {
        "endpoint_url": os.environ["R2_ENDPOINT_URL"],
        "access_key": os.environ["R2_ACCESS_KEY_ID"],
        "secret_key": os.environ["R2_SECRET_ACCESS_KEY"],
        "bucket": os.environ["R2_BUCKET_NAME"],
    }

r2_config = load_r2_config()

s3_client = boto3.client(
    "s3",
    endpoint_url=r2_config["endpoint_url"],
    aws_access_key_id=r2_config["access_key"],
    aws_secret_access_key=r2_config["secret_key"],
    config=Config(signature_version="s3v4"),
)

R2_BUCKET_NAME = r2_config["bucket"]

REDIS_DOCUMENT_STREAM = "events:new_document"
ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain", "text/markdown"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.get("/knowledge/documents", tags=["Knowledge"])
async def list_documents_for_user(
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    user_id: str = Depends(get_current_user_id),
):
    """
    Lists all documents uploaded by the current user.
    """
    try:
        documents = await supabase_adapter.get_documents_for_user(user_id=user_id)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/upload", tags=["Knowledge"])
async def upload_knowledge_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """
    Uploads a knowledge document, stores it in R2, creates a record in Supabase,
    and publishes an event to Redis for processing.
    """
    redis_client = request.app.state.redis

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large.")

    # 1. Get the agent for the user to associate the document
    agent = await supabase_adapter.get_agent_for_user(user_id=user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No active agent found for this user. Please configure an agent first.")

    agent_id = agent['id']

    # 2. Upload file to R2
    storage_path = f"{user_id}/{uuid.uuid4()}-{file.filename}"
    try:
        s3_client.upload_fileobj(file.file, R2_BUCKET_NAME, storage_path)
    except Exception as e:
        logger.error("Error uploading file to R2: %s", e)
        raise HTTPException(status_code=500, detail="Failed to upload file to storage.")

    # 3. Create document record in Supabase
    document_record = await supabase_adapter.create_document_record(
        user_id=user_id,
        agent_id=agent_id,
        file_name=file.filename,
        storage_path=storage_path
    )
    if not document_record:
        try:
            s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=storage_path)
        except Exception as e:
            logger.error("Error deleting file from R2 after DB failure: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create document record in database.")

    document_id = document_record['id']

    # 4. Publish event to Redis
    try:
        event_payload = {
            "document_id": document_id,
            "storage_path": storage_path,
            "user_id": user_id,
        }
        await redis_client.xadd(REDIS_DOCUMENT_STREAM, event_payload, maxlen=10000, approximate=True)
    except Exception as e:
        try:
            s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=storage_path)
        except Exception as s3e:
            logger.error("Error deleting file from R2 after Redis failure: %s", s3e)
        try:
            await supabase_adapter.delete_document(document_id)
        except Exception as dbe:
            logger.error("Error deleting document record after Redis failure: %s", dbe)
        logger.error("Error publishing document event to Redis: %s", e)
        raise HTTPException(status_code=500, detail="Failed to queue document for processing.")

    return {"status": "ok", "message": "File uploaded and queued for processing.", "document_id": document_id}
