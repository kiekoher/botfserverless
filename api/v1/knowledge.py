import uuid
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from dependencies import get_current_user_id, get_supabase_adapter, cloudflare_queue_adapter
from infrastructure.supabase_adapter import SupabaseAdapter
from infrastructure.cloudflare_queue_adapter import CloudflareQueueAdapter

router = APIRouter()
logger = logging.getLogger(__name__)

# NOTE: Direct R2 client logic has been removed. The API now queues a message
# for a worker to handle document processing and embedding. The worker will
# be responsible for interacting with R2 if needed, though typically the
# embedding worker just needs the text content.

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
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    supabase_adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    queue_adapter: CloudflareQueueAdapter = Depends(lambda: cloudflare_queue_adapter)
):
    """
    Uploads a knowledge document, creates a record in Supabase,
    and publishes an event to a queue for processing by the embedding worker.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large.")

    agent = await supabase_adapter.get_agent_for_user(user_id=user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No active agent found for this user.")
    agent_id = agent['id']

    # In this new flow, we pass the text content directly to the embedding worker.
    # We no longer upload the raw file to R2 from the API. The worker can decide
    # if it needs to parse it (e.g. PDF) or just use the text.
    # For simplicity, we assume the worker handles text content for now.

    # For PDF, a more complex worker would be needed to extract text first.
    if file.content_type == "application/pdf":
        # This would be a more complex flow handled by a specific document processing worker
        # For now, we'll treat it as an error or unsupported path.
        raise HTTPException(status_code=501, detail="PDF processing not implemented in this flow.")

    text_content = file_content.decode('utf-8')

    document_record = await supabase_adapter.create_document_record(
        user_id=user_id,
        agent_id=agent_id,
        file_name=file.filename,
        storage_path=f"text_content_sha256/{uuid.uuid4()}" # Placeholder path
    )
    if not document_record:
        raise HTTPException(status_code=500, detail="Failed to create document record in database.")
    document_id = document_record['id']

    try:
        event_payload = {
            "document_id": document_id,
            "text": text_content,
        }
        await queue_adapter.publish_message(event_payload)
    except Exception as e:
        await supabase_adapter.delete_document(document_id)
        logger.error(f"Error publishing document event to queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue document for processing.")

    return {"status": "ok", "message": "Document content queued for embedding.", "document_id": document_id}
