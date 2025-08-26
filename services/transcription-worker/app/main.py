import asyncio
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

import boto3
from faster_whisper import WhisperModel
from pydub import AudioSegment
from redis.asyncio import Redis
from redis.exceptions import ResponseError
from tenacity import retry, stop_after_attempt, wait_random_exponential

sys.path.append(str(Path(__file__).resolve().parents[2]))
from common.r2_config import load_r2_config

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{REDIS_HOST}:6379"
STREAM_IN = "events:new_message"
STREAM_OUT = "events:transcribed_message"
CONSUMER_GROUP = "group:transcription-workers"
CONSUMER_NAME = f"consumer:transcription-worker-{os.getpid()}"
HEALTHCHECK_FILE = Path("/tmp/health/last_processed")
DEAD_LETTER_QUEUE = "events:dead_letter_queue"
MODEL_SIZE = "base"
COMPUTE_TYPE = "int8"
DEVICE = "cpu"

# --- Tenacity Retry Configuration ---
RETRY_STRATEGY = retry(
    wait=wait_random_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(4)
)
ASYNC_RETRY_STRATEGY = retry(
    wait=wait_random_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(4)
)

# --- Initialize Clients ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🤖 Transcription Worker starting...")
s3_client = None
whisper_model = None
_r2_cfg = load_r2_config()
R2_BUCKET_NAME = _r2_cfg["bucket"]

# --- Helper Functions ---

async def touch_healthcheck_file():
    """Updates the modification time of the healthcheck file."""
    try:
        HEALTHCHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(HEALTHCHECK_FILE.touch)
    except Exception as e:
        logger.warning("Could not touch healthcheck file: %s", e)

@ASYNC_RETRY_STRATEGY
async def create_redis_client():
    """Creates a Redis client with async retry logic."""
    try:
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        await client.ping()
        logger.info("✅ Redis client connected.")
        return client
    except Exception as e:
        logger.error("Redis connection error, retrying...: %s", e)
        raise

@RETRY_STRATEGY
def create_s3_client():
    """Creates an S3 client with retry logic."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=_r2_cfg["endpoint_url"],
            aws_access_key_id=_r2_cfg["access_key"],
            aws_secret_access_key=_r2_cfg["secret_key"],
            region_name="auto",
        )
        s3.list_buckets()
        logger.info("✅ R2 S3 client initialized.")
        return s3
    except Exception as e:
        logger.error("Failed to initialize R2 Storage client, retrying...: %s", e)
        raise

def initialize_whisper_model():
    """Initializes the Whisper model."""
    try:
        logger.info("Loading Whisper model '%s'...", MODEL_SIZE)
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        logger.info("✅ Whisper model loaded.")
        return model
    except Exception as e:
        logger.error("❌ Failed to initialize Whisper model: %s", e)
        raise

@RETRY_STRATEGY
def download_audio_from_r2_sync(file_key):
    """Downloads an audio file from R2 and returns its local path."""
    if not s3_client:
        raise Exception("S3 client not initialized.")
    fd, temp_local_path = tempfile.mkstemp(suffix=".ogg")
    os.close(fd)
    s3_client.download_file(R2_BUCKET_NAME, file_key, temp_local_path)
    logger.info("Downloaded '%s' to '%s'", file_key, temp_local_path)
    return temp_local_path

def transcribe_audio_sync(file_path):
    """Transcribes the audio file at the given path using Whisper."""
    if not whisper_model:
        raise Exception("Whisper model not initialized.")
    wav_path = None
    try:
        ogg_audio = AudioSegment.from_file(file_path, format="ogg")
        wav_path = file_path.replace(".ogg", ".wav")
        ogg_audio.export(wav_path, format="wav")

        logger.info("Starting transcription for %s...", wav_path)
        segments, info = whisper_model.transcribe(wav_path, beam_size=5, language="es")
        logger.info("Detected language '%s' with probability %s", info.language, info.language_probability)
        transcription = "".join(segment.text for segment in segments)
        return transcription.strip()
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if wav_path and os.path.exists(wav_path): os.remove(wav_path)

@ASYNC_RETRY_STRATEGY
async def publish_transcription(redis_client: Redis, payload: dict):
    """Publishes the transcribed message to the output stream with retry logic."""
    try:
        await redis_client.xadd(STREAM_OUT, payload, maxlen=10000, approximate=True)
    except Exception as e:
        logger.error("Failed to publish to stream %s, retrying...: %s", STREAM_OUT, e)
        raise

async def setup_redis(redis_client: Redis):
    """Create consumer group if it doesn't exist."""
    try:
        await redis_client.xgroup_create(STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info("Consumer group '%s' created.", CONSUMER_GROUP)
    except ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info("Consumer group '%s' already exists.", CONSUMER_GROUP)
        else:
            raise

async def process_message(message_id: str, message_data: dict):
    """Processes a single message, with retries on network operations."""
    body_text = ""
    transcribed = "false"

    if message_data.get("mediaKey"):
        logger.info("Message has media, attempting transcription...")
        local_path = await asyncio.to_thread(download_audio_from_r2_sync, message_data["mediaKey"])
        if local_path:
            body_text = await asyncio.to_thread(transcribe_audio_sync, local_path)
            transcribed = "true"
            logger.info("Transcription successful: '%s'", body_text)
        else:
            raise Exception("Failed to download audio from R2 after retries.")
    else:
        body_text = message_data["body"]

    output_payload = {
        "userId": message_data["userId"],
        "chatId": message_data["chatId"],
        "timestamp": message_data["timestamp"],
        "body": body_text,
        "transcribed": transcribed,
    }

    await publish_transcription(redis_client, output_payload)
    logger.info("Forwarded message for %s to %s", message_data['userId'], STREAM_OUT)

async def main():
    """Main function to set up clients and run the consumer loop."""
    global s3_client, whisper_model
    s3_client = create_s3_client()
    whisper_model = await asyncio.to_thread(initialize_whisper_model)
    if not s3_client or not whisper_model:
        logger.error("Cannot start worker without external clients. Exiting.")
        return

    global redis_client
    redis_client = await create_redis_client()
    await setup_redis(redis_client)

    logger.info("Starting to listen for messages...")
    while True:
        try:
            await touch_healthcheck_file()

            response = await redis_client.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {STREAM_IN: ">"}, count=1, block=5000
            )
            if not response:
                continue

            for stream, messages in response:
                for message_id, message_data in messages:
                    logger.info("Received message %s", message_id)
                    try:
                        await process_message(message_id, message_data)
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        logger.info("Successfully processed and acknowledged message %s", message_id)
                    except Exception as e:
                        logger.error("Failed to process message %s after all retries: %s. Moving to DLQ.", message_id, e)
                        dlq_payload = message_data.copy()
                        dlq_payload["error_service"] = "transcription-worker"
                        dlq_payload["error_timestamp"] = str(time.time())
                        dlq_payload["error_details"] = str(e)
                        await redis_client.xadd(DEAD_LETTER_QUEUE, dlq_payload, maxlen=10000, approximate=True)
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.error("A critical error occurred in main loop: %s", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
