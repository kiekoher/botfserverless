import os
import redis
import time
import tempfile
from google.cloud import speech
from google.cloud import storage

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
STREAM_IN = "events:new_message"
STREAM_OUT = "events:transcribed_message"
CONSUMER_GROUP = "group:transcription-workers"
CONSUMER_NAME = f"consumer:transcription-worker-1"

# Google Cloud / R2 Configuration
# For R2, we use the GCS client with a custom endpoint.
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL") # e.g., https://<accountid>.r2.cloudflarestorage.com
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

# --- Initialize Clients ---
print("🤖 Transcription Worker starting...")

# Redis Client
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Google Cloud Storage Client (for R2)
# The GCS client can be used with any S3-compatible API like R2
# by providing the endpoint_url and credentials.
try:
    storage_client = storage.Client(
        endpoint_url=R2_ENDPOINT_URL,
        project="r2-project", # project is required but not used by R2
        credentials=storage.credentials.Credentials(
            access_token=R2_ACCESS_KEY_ID, # This is a bit of a hack for the library
            client_id=R2_ACCESS_KEY_ID,
            client_secret=R2_SECRET_ACCESS_KEY,
            token_uri="https://oauth2.googleapis.com/token", # Dummy value
        )
    )
    print("✅ R2 Storage client initialized.")
except Exception as e:
    print(f"❌ Failed to initialize R2 Storage client: {e}")
    storage_client = None


# Google Speech-to-Text Client
try:
    # The environment variable GOOGLE_APPLICATION_CREDENTIALS should be set
    # in the Docker environment to point to the service account JSON key.
    speech_client = speech.SpeechClient()
    print("✅ Google Speech-to-Text client initialized.")
except Exception as e:
    print(f"❌ Failed to initialize Speech-to-Text client: {e}")
    speech_client = None

# --- Helper Functions ---
def download_audio_from_r2(file_key):
    """Downloads an audio file from R2 and returns its local path."""
    if not storage_client:
        raise Exception("Storage client not initialized.")
    try:
        bucket = storage_client.bucket(R2_BUCKET_NAME)
        blob = bucket.blob(file_key)

        # Download to a temporary file
        _, temp_local_path = tempfile.mkstemp()
        blob.download_to_filename(temp_local_path)
        print(f"Downloaded '{file_key}' to '{temp_local_path}'")
        return temp_local_path
    except Exception as e:
        print(f"❌ Failed to download file from R2: {e}")
        return None

def transcribe_audio(file_path):
    """Transcribes the audio file at the given path."""
    if not speech_client:
        raise Exception("Speech client not initialized.")
    try:
        with open(file_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS, # Common for WhatsApp
            sample_rate_hertz=16000,
            language_code="es-ES", # Spanish
        )

        response = speech_client.recognize(config=config, audio=audio)

        if response.results:
            transcription = response.results[0].alternatives[0].transcript
            print(f"Transcription successful: '{transcription}'")
            return transcription
        else:
            print("No transcription result from API.")
            return ""
    except Exception as e:
        print(f"❌ Failed to transcribe audio: {e}")
        return ""
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Main Loop ---
def setup_redis():
    """Create consumer group if it doesn't exist."""
    try:
        r.xgroup_create(STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True)
        print(f"Consumer group '{CONSUMER_GROUP}' created.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{CONSUMER_GROUP}' already exists.")
        else:
            raise

def main_loop():
    print("👂 Starting to listen for messages...")
    while True:
        try:
            response = r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_IN: ">"},
                count=1,
                block=5000
            )

            if not response:
                continue

            for stream, messages in response:
                for message_id, message_data in messages:
                    print(f"Received message {message_id}: {message_data}")

                    body_text = ""
                    transcribed = "false"

                    if 'mediaKey' in message_data and message_data['mediaKey']:
                        print("🎤 Message has media, attempting transcription...")
                        # Download from R2
                        local_path = download_audio_from_r2(message_data['mediaKey'])
                        if local_path:
                            # Transcribe
                            body_text = transcribe_audio(local_path)
                            transcribed = "true"
                        else:
                            body_text = "[Error during audio download]"
                    else:
                        # It's a regular text message
                        body_text = message_data['body']


                    output_payload = {
                        'userId': message_data['userId'],
                        'chatId': message_data['chatId'],
                        'timestamp': message_data['timestamp'],
                        'body': body_text,
                        'transcribed': transcribed
                    }

                    r.xadd(STREAM_OUT, output_payload)
                    print(f"✅ Forwarded message for {message_data['userId']} to {STREAM_OUT}")

                    r.xack(STREAM_IN, CONSUMER_GROUP, message_id)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    setup_redis()
    main_loop()
