import os
import time
import tempfile
import asyncio
import boto3
from redis.asyncio import Redis
from redis.exceptions import ResponseError
from faster_whisper import WhisperModel
from pydub import AudioSegment

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{REDIS_HOST}:6379"
STREAM_IN = "events:new_message"
STREAM_OUT = "events:transcribed_message"
CONSUMER_GROUP = "group:transcription-workers"
CONSUMER_NAME = f"consumer:transcription-worker-{os.getpid()}"

# R2 Configuration
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

# Dead Letter Queue
DEAD_LETTER_QUEUE = "events:dead_letter_queue"
MAX_RETRIES = 3

# Whisper Model Configuration
MODEL_SIZE = "base"  # Use "base", "small", "medium", "large-v2"
COMPUTE_TYPE = "int8" # "float16", "int8", etc.
DEVICE = "cpu"

# --- Initialize Clients ---
print("🤖 Transcription Worker starting...")
s3_client = None
whisper_model = None


def initialize_external_clients():
    """Initializes non-async clients. Can be run in an executor."""
    global s3_client, whisper_model
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        print("✅ R2 S3 client initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize R2 Storage client: {e}")

    try:
        print(f"Loading Whisper model '{MODEL_SIZE}'...")
        whisper_model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        print("✅ Whisper model loaded.")
    except Exception as e:
        print(f"❌ Failed to initialize Whisper model: {e}")


# --- Helper Functions (Blocking) ---
def download_audio_from_r2_sync(file_key):
    """Downloads an audio file from R2 and returns its local path."""
    if not s3_client:
        raise Exception("S3 client not initialized.")
    fd, temp_local_path = tempfile.mkstemp(suffix=".ogg")
    os.close(fd)
    s3_client.download_file(R2_BUCKET_NAME, file_key, temp_local_path)
    print(f"Downloaded '{file_key}' to '{temp_local_path}'")
    return temp_local_path


def transcribe_audio_sync(file_path):
    """Transcribes the audio file at the given path using Whisper."""
    if not whisper_model:
        raise Exception("Whisper model not initialized.")

    wav_path = None
    try:
        # Convert OGG to WAV, which is preferred by Whisper
        ogg_audio = AudioSegment.from_file(file_path, format="ogg")
        wav_path = file_path.replace(".ogg", ".wav")
        ogg_audio.export(wav_path, format="wav")

        print(f"Starting transcription for {wav_path}...")
        segments, info = whisper_model.transcribe(wav_path, beam_size=5, language="es")

        print(f"Detected language '{info.language}' with probability {info.language_probability}")

        transcription = "".join(segment.text for segment in segments)
        return transcription.strip()
    finally:
        # Clean up both the original and converted files
        if os.path.exists(file_path):
            os.remove(file_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


# --- Main Async Logic ---
async def setup_redis(redis_client: Redis):
    """Create consumer group if it doesn't exist."""
    try:
        await redis_client.xgroup_create(
            STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True
        )
        print(f"Consumer group '{CONSUMER_GROUP}' created.")
    except ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{CONSUMER_GROUP}' already exists.")
        else:
            raise


async def process_message_with_retry(redis_client: Redis, message_id, message_data):
    """Process a message with a retry mechanism."""
    for attempt in range(MAX_RETRIES):
        try:
            print(
                f"Processing message {message_id}, attempt {attempt + 1}/{MAX_RETRIES}"
            )
            body_text = ""
            transcribed = "false"

            if message_data.get("mediaKey"):
                print("🎤 Message has media, attempting transcription...")
                # Run blocking I/O in a thread pool
                local_path = await asyncio.to_thread(
                    download_audio_from_r2_sync, message_data["mediaKey"]
                )
                if local_path:
                    # Run CPU-bound/blocking transcription in a thread pool
                    body_text = await asyncio.to_thread(
                        transcribe_audio_sync, local_path
                    )
                    transcribed = "true"
                    print(f"Transcription successful: '{body_text}'")
                else:
                    body_text = "[Error during audio download]"
                    raise Exception("Failed to download audio from R2")
            else:
                body_text = message_data["body"]

            output_payload = {
                "userId": message_data["userId"],
                "chatId": message_data["chatId"],
                "timestamp": message_data["timestamp"],
                "body": body_text,
                "transcribed": transcribed,
            }

            await redis_client.xadd(STREAM_OUT, output_payload)
            print(f"✅ Forwarded message for {message_data['userId']} to {STREAM_OUT}")
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
            await asyncio.sleep(2**attempt)
    return False


async def main():
    """Main function to set up clients and run the consumer loop."""
    # Initialize blocking clients in an executor to not block the event loop on startup
    await asyncio.to_thread(initialize_external_clients)
    if not s3_client or not whisper_model:
        print("❌ Cannot start worker without external clients. Exiting.")
        return

    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    await setup_redis(redis_client)

    print("👂 Starting to listen for messages...")
    while True:
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
                        dlq_payload["error_service"] = "transcription-worker"
                        dlq_payload["error_timestamp"] = str(time.time())
                        await redis_client.xadd(DEAD_LETTER_QUEUE, dlq_payload)
                        await redis_client.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        print(
                            f"Moved message {message_id} to DLQ '{DEAD_LETTER_QUEUE}'"
                        )

        except Exception as e:
            print(f"A critical error occurred in main loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
