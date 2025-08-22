import os
import time
import redis
import boto3
import openai
import tiktoken
import io
from PyPDF2 import PdfReader
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Initialization ---
load_dotenv()
print("🤖 Embedding Worker Initializing...")

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
STREAM_IN = "events:new_document"
CONSUMER_GROUP = "group:embedding-worker"
CONSUMER_NAME = "consumer:embedding-worker-1"
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Supabase (using Service Role Key to bypass RLS)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("🔌 Supabase client created with service role.")

# R2/S3
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
s3_client = boto3.client('s3', endpoint_url=R2_ENDPOINT_URL, aws_access_key_id=R2_ACCESS_KEY_ID, aws_secret_access_key=R2_SECRET_ACCESS_KEY)

# OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"

# Tiktoken for chunking
tokenizer = tiktoken.get_encoding("cl100k_base")
MAX_TOKENS_PER_CHUNK = 500 # A reasonable chunk size

# --- Helper Functions ---

def update_document_status(doc_id: str, status: str):
    try:
        supabase.table("documents").update({"status": status}).eq("id", doc_id).execute()
        print(f"Updated document {doc_id} status to {status}")
    except Exception as e:
        print(f"❌ Error updating document status for {doc_id}: {e}")

def get_text_from_storage(storage_path: str) -> str:
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

def chunk_text(text: str) -> list[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), MAX_TOKENS_PER_CHUNK):
        chunk_tokens = tokens[i:i + MAX_TOKENS_PER_CHUNK]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    print(f"Split text into {len(chunks)} chunks.")
    return chunks

def get_embeddings(texts: list[str]) -> list[list[float]]:
    response = openai.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in response.data]

# --- Main Worker Loop ---

def main():
    print("Creating consumer group if it doesn't exist...")
    try:
        redis_client.xgroup_create(STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{CONSUMER_GROUP}' already exists.")
        else:
            raise

    print(f"👂 Worker started. Listening for events on '{STREAM_IN}'...")
    while True:
        try:
            response = redis_client.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {STREAM_IN: ">"}, count=1, block=5000
            )
            if not response:
                continue

            message_id = response[0][1][0][0]
            message_data = response[0][1][0][1]
            doc_id = message_data.get("document_id")
            storage_path = message_data.get("storage_path")
            user_id = message_data.get("user_id")

            print(f"Processing document {doc_id} from {storage_path}")
            update_document_status(doc_id, "processing")

            try:
                # 1. Get text from document
                text_content = get_text_from_storage(storage_path)

                # 2. Split text into chunks
                text_chunks = chunk_text(text_content)

                # 3. Get embeddings for chunks
                embeddings = get_embeddings(text_chunks)

                # 4. Save to Supabase
                records_to_insert = []
                for i, chunk in enumerate(text_chunks):
                    records_to_insert.append({
                        "document_id": doc_id,
                        "user_id": user_id,
                        "content": chunk,
                        "embedding": embeddings[i]
                    })

                supabase.table("document_chunks").insert(records_to_insert).execute()
                print(f"✅ Successfully inserted {len(records_to_insert)} chunks for document {doc_id}")

                # 5. Mark as complete
                update_document_status(doc_id, "completed")

            except Exception as e:
                print(f"❌ Failed to process document {doc_id}: {e}")
                update_document_status(doc_id, "failed")

            redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)

        except Exception as e:
            print(f"🚨 Critical error in worker loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
