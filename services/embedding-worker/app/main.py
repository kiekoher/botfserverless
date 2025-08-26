import io
import logging
import os
import sys
import time
from pathlib import Path

import boto3
import redis
from openai import APIError, OpenAI, RateLimitError, Timeout
from PyPDF2 import PdfReader
from supabase import Client, create_client
from tenacity import retry, stop_after_attempt, wait_random_exponential

from chunking import chunk_text

sys.path.append(str(Path(__file__).resolve().parents[2]))
from common.r2_config import load_r2_config

# --- Initialization ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🤖 Embedding Worker Initializing...")

HEALTHCHECK_FILE = Path("/tmp/health/last_processed")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
STREAM_IN = "events:new_document"
CONSUMER_GROUP = "group:embedding-worker"
CONSUMER_NAME = f"consumer:embedding-worker-{os.getenv('HOSTNAME', '1')}"
DEAD_LETTER_QUEUE = "events:dead_letter_queue"

# --- Tenacity Retry Configuration ---
# A generic retry strategy for transient network or service errors.
# Stops after 4 attempts with exponential backoff (e.g., 1s, 2s, 4s, 8s).
RETRY_STRATEGY = retry(
    wait=wait_random_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(4)
)

# A specific retry strategy for OpenAI API calls, which can be sensitive to rate limits.
OPENAI_RETRY_STRATEGY = retry(
    wait=wait_random_exponential(multiplier=2, max=30),
    stop=stop_after_attempt(5)
)

# --- Client Initialization with Retries ---

@RETRY_STRATEGY
def create_redis_client():
    """Creates a Redis client, retrying on connection errors."""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        logger.info("✅ Redis client connected.")
        return client
    except Exception as e:
        logger.error("Redis connection error, retrying...: %s", e)
        raise

redis_client = create_redis_client()

# Supabase client (no retry on creation, it's just a config object)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("🔌 Supabase client created.")

# R2/S3 client
r2_config = load_r2_config()
R2_BUCKET_NAME = r2_config["bucket"]

@RETRY_STRATEGY
def create_s3_client():
    """Creates an S3 client, retrying on connection errors."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=r2_config["endpoint_url"],
            aws_access_key_id=r2_config["access_key"],
            aws_secret_access_key=r2_config["secret_key"],
        )
        s3.list_buckets()  # A quick check to ensure credentials are valid
        logger.info("✅ R2/S3 client connected.")
        return s3
    except Exception as e:
        logger.error("R2/S3 client error, retrying...: %s", e)
        raise

s3_client = create_s3_client()

# OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# --- Helper Functions with Retries ---

def touch_healthcheck_file():
    """Updates the modification time of the healthcheck file."""
    try:
        HEALTHCHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEALTHCHECK_FILE.touch()
    except Exception as e:
        logger.warning("Could not touch healthcheck file: %s", e)

@RETRY_STRATEGY
def update_document_status(doc_id: str, status: str):
    """Updates document status in Supabase with retry logic."""
    try:
        supabase.table("documents").update({"status": status}).eq("id", doc_id).execute()
        logger.info("Updated document %s status to %s", doc_id, status)
    except Exception as e:
        logger.error("Error updating document status for %s, retrying...: %s", doc_id, e)
        raise

MAX_FILE_SIZE_MB = 10

@RETRY_STRATEGY
def get_text_from_storage(storage_path: str) -> str:
    """Gets file content from R2/S3 storage with retry logic."""
    try:
        head = s3_client.head_object(Bucket=R2_BUCKET_NAME, Key=storage_path)
        size = head.get("ContentLength", 0)
        if size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB")

        obj = s3_client.get_object(Bucket=R2_BUCKET_NAME, Key=storage_path)
        content = obj['Body'].read()

        if storage_path.lower().endswith('.pdf'):
            text = ""
            with io.BytesIO(content) as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        elif storage_path.lower().endswith('.txt'):
            return content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {storage_path}")
    except Exception as e:
        logger.error("Error getting text from storage for %s, retrying...: %s", storage_path, e)
        raise

@OPENAI_RETRY_STRATEGY
def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Gets embeddings from OpenAI with a specific retry strategy."""
    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]
    except (RateLimitError, Timeout, APIError) as e:
        logger.warning("OpenAI API error, retrying...: %s", e)
        raise
    except Exception as e:
        logger.error("Non-retriable OpenAI embedding error: %s", e)
        raise

@RETRY_STRATEGY
def insert_document_chunks(records_to_insert: list[dict]):
    """Inserts document chunks into Supabase with retry logic."""
    try:
        supabase.table("document_chunks").insert(records_to_insert).execute()
    except Exception as e:
        logger.error("Error inserting document chunks, retrying...: %s", e)
        raise

# --- Main Worker Loop ---

def main():
    logger.info("Creating consumer group if it doesn't exist...")
    try:
        redis_client.xgroup_create(STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info("Consumer group '%s' already exists.", CONSUMER_GROUP)
        else:
            raise

    logger.info("👂 Worker started. Listening for events on '%s'...", STREAM_IN)
    while True:
        try:
            touch_healthcheck_file()
            response = redis_client.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {STREAM_IN: ">"}, count=1, block=5000
            )
            if not response:
                continue

            message_id = response[0][1][0][0]
            message_data = response[0][1][0][1]

            process_document(message_data)
            redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.error("Critical error in worker loop: %s", e)
            time.sleep(5)

def process_document(message_data: dict) -> bool:
    """Process a single document message."""
    doc_id = message_data.get("document_id")
    storage_path = message_data.get("storage_path")
    user_id = message_data.get("user_id")

    logger.info("Processing document %s from %s", doc_id, storage_path)
    try:
        update_document_status(doc_id, "processing")
        text_content = get_text_from_storage(storage_path)
        text_chunks = chunk_text(text_content)
        embeddings = get_embeddings(text_chunks)

        records_to_insert = []
        for i, chunk in enumerate(text_chunks):
            records_to_insert.append({
                "document_id": doc_id,
                "user_id": user_id,
                "content": chunk,
                "embedding": embeddings[i],
            })

        insert_document_chunks(records_to_insert)
        logger.info("✅ Successfully inserted %d chunks for document %s", len(records_to_insert), doc_id)
        update_document_status(doc_id, "completed")
        return True
    except Exception as e:
        logger.error("Failed to process document %s after all retries: %s", doc_id, e)
        update_document_status(doc_id, "failed")
        dlq_payload = message_data.copy()
        dlq_payload["error"] = str(e)
        dlq_payload["error_service"] = "embedding-worker"
        dlq_payload["error_timestamp"] = str(time.time())
        redis_client.xadd(DEAD_LETTER_QUEUE, dlq_payload, maxlen=10000, approximate=True)
        return False

if __name__ == "__main__":
    main()
