import os
import time
import redis
import boto3
from openai import OpenAI, RateLimitError
import io
import logging
from PyPDF2 import PdfReader
from supabase import create_client, Client
from chunking import chunk_text
from pathlib import Path

# --- Initialization ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🤖 Embedding Worker Initializing...")

# Healthcheck file
HEALTHCHECK_FILE = Path("/tmp/health/last_processed")

# Redis with reconnection
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
STREAM_IN = "events:new_document"
CONSUMER_GROUP = "group:embedding-worker"
CONSUMER_NAME = f"consumer:embedding-worker-{os.getenv('HOSTNAME', '1')}"
DEAD_LETTER_QUEUE = "events:dead_letter_queue"
MAX_RETRIES = 3

def create_redis_client(retry=0):
    delay = min(2 ** retry, 30)
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.error("Redis connection error: %s", e)
        time.sleep(delay)
        return create_redis_client(retry + 1)

redis_client = create_redis_client()

# Supabase client (use restricted service key for embeddings)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("🔌 Supabase client created with limited permissions.")

def load_r2_config() -> dict[str, str]:
    required = [
        "R2_ENDPOINT_URL",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
    ]
    missing = [k for k in required if not os.environ.get(k)]
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
R2_BUCKET_NAME = r2_config['bucket']

def create_s3_client(retry=0):
    delay = min(2 ** retry, 30)
    try:
        return boto3.client(
            "s3",
            endpoint_url=r2_config["endpoint_url"],
            aws_access_key_id=r2_config["access_key"],
            aws_secret_access_key=r2_config["secret_key"],
        )
    except Exception as e:
        logger.error("R2 client error: %s", e)
        time.sleep(delay)
        return create_s3_client(retry + 1)

s3_client = create_s3_client()
# OpenAI
client = OpenAI()
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# --- Helper Functions ---

def touch_healthcheck_file():
    """Updates the modification time of the healthcheck file."""
    try:
        HEALTHCHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEALTHCHECK_FILE.touch()
    except Exception as e:
        logger.warning("Could not touch healthcheck file: %s", e)


def update_document_status(doc_id: str, status: str):
    try:
        supabase.table("documents").update({"status": status}).eq("id", doc_id).execute()
        logger.info("Updated document %s status to %s", doc_id, status)
    except Exception as e:
        logger.error("Error updating document status for %s: %s", doc_id, e)

MAX_FILE_SIZE_MB = 10

def get_text_from_storage(storage_path: str) -> str:
    head = s3_client.head_object(Bucket=R2_BUCKET_NAME, Key=storage_path)
    size = head.get("ContentLength", 0)
    if size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError("File exceeds maximum allowed size of 10MB")

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

def get_embeddings(texts: list[str], max_retries: int = 3) -> list[list[float]]:
    delay = 5
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [item.embedding for item in response.data]
        except RateLimitError as e:
            logger.warning(
                "Rate limit hit while requesting embeddings (attempt %s/%s): %s",
                attempt + 1,
                max_retries,
                e,
            )
            if attempt + 1 == max_retries:
                raise
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            logger.error("OpenAI embedding error: %s", e)
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
            # Touch the healthcheck file at the beginning of each loop iteration
            # to signal that the worker is alive and polling.
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
    update_document_status(doc_id, "processing")

    try:
        text_content = get_text_from_storage(storage_path)
        text_chunks = chunk_text(text_content)
        embeddings = get_embeddings(text_chunks)

        records_to_insert = []
        for i, chunk in enumerate(text_chunks):
            records_to_insert.append(
                {
                    "document_id": doc_id,
                    "user_id": user_id,
                    "content": chunk,
                    "embedding": embeddings[i],
                }
            )

        supabase.table("document_chunks").insert(records_to_insert).execute()
        logger.info(
            "Successfully inserted %d chunks for document %s",
            len(records_to_insert),
            doc_id,
        )
        update_document_status(doc_id, "completed")
        return True
    except Exception as e:
        logger.error("Failed to process document %s: %s", doc_id, e)
        update_document_status(doc_id, "failed")
        dlq_payload = message_data.copy()
        dlq_payload["error"] = str(e)
        dlq_payload["error_service"] = "embedding-worker"
        dlq_payload["error_timestamp"] = str(time.time())
        redis_client.xadd(
            DEAD_LETTER_QUEUE,
            dlq_payload,
            maxlen=10000,
            approximate=True,
        )
        return False

if __name__ == "__main__":
    main()
