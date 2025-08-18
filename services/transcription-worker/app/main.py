import os
import redis
import time

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
STREAM_IN = "events:new_message"
STREAM_OUT = "events:transcribed_message"
CONSUMER_GROUP = "group:transcription-workers"
CONSUMER_NAME = f"consumer:transcription-worker-1"

print("🤖 Transcription Worker starting...")

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Create the consumer group
try:
    r.xgroup_create(STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True)
    print(f"Consumer group '{CONSUMER_GROUP}' created.")
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" in str(e):
        print(f"Consumer group '{CONSUMER_GROUP}' already exists.")
    else:
        raise

print("👂 Starting to listen for messages...")

while True:
    try:
        # Read from the stream
        response = r.xreadgroup(
            CONSUMER_GROUP,
            CONSUMER_NAME,
            {STREAM_IN: ">"},
            count=1,
            block=5000
        )

        if response:
            for stream, messages in response:
                for message_id, message_data in messages:
                    print(f"Received message {message_id}: {message_data}")

                    # In a real scenario, we would check if it's an audio message.
                    # For now, we assume it's text and pass it through.
                    # Later, we will add logic to download audio, transcribe,
                    # and then publish the text.

                    # For now, just forward the message body.
                    # The main-api will expect a consistent format.
                    output_payload = {
                        'userId': message_data['userId'],
                        'chatId': message_data['chatId'],
                        'timestamp': message_data['timestamp'],
                        'body': message_data['body'], # This would be the transcribed text
                        'transcribed': 'false' # a flag to indicate if it was a transcription
                    }

                    r.xadd(STREAM_OUT, output_payload)
                    print(f"Forwarded message to {STREAM_OUT}")

                    # Acknowledge the message
                    r.xack(STREAM_IN, CONSUMER_GROUP, message_id)

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)
