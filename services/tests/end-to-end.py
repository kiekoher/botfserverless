import redis
import time
import os
import uuid

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
STREAM_IN = "events:new_message"
STREAM_OUT = "events:message_out"
TEST_TIMEOUT = 60  # seconds

def run_test():
    """
    Runs an end-to-end test of the message processing pipeline.
    1. Connects to Redis.
    2. Publishes a test message to the input stream.
    3. Listens on the output stream for the processed response.
    4. Verifies the response and exits with success or failure.
    """
    print("--- Starting End-to-End Test ---")

    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis successfully.")
    except redis.exceptions.ConnectionError as e:
        print(f"❌ Could not connect to Redis: {e}")
        exit(1)

    # Unique identifier for this test run
    test_id = str(uuid.uuid4())
    user_id = f"test-user-{test_id}"
    chat_id = f"test-chat-{test_id}"
    message_body = "Hola, ¿cómo estás?"

    # 1. Publish test message
    test_message = {
        'userId': user_id,
        'chatId': chat_id,
        'timestamp': str(time.time()),
        'body': message_body,
        'mediaKey': None
    }
    r.xadd(STREAM_IN, test_message)
    print(f"📥 Published test message to '{STREAM_IN}' for user '{user_id}'.")

    # 2. Listen for the response
    print(f"👂 Listening on '{STREAM_OUT}' for a response...")
    start_time = time.time()

    # Create a unique consumer group for this test run to avoid conflicts
    consumer_group = f"group:e2e-test-{test_id}"
    consumer_name = f"consumer:e2e-test-{test_id}"
    try:
        r.xgroup_create(STREAM_OUT, consumer_group, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
             print(f"❌ Error creating consumer group: {e}")
             exit(1)


    while time.time() - start_time < TEST_TIMEOUT:
        response = r.xreadgroup(
            consumer_group,
            consumer_name,
            {STREAM_OUT: ">"},
            count=1,
            block=2000
        )

        if not response:
            continue

        for _, messages in response:
            for message_id, message_data in messages:
                print(f"Received message on '{STREAM_OUT}': {message_data}")
                # 3. Verify the response
                if message_data.get('userId') == user_id:
                    print("✅ Verification successful: Found matching userId.")
                    print("--- End-to-End Test Passed ---")
                    r.xgroup_destroy(STREAM_OUT, consumer_group)
                    exit(0)
                else:
                    # Acknowledge messages that aren't ours and continue
                    r.xack(STREAM_OUT, consumer_group, message_id)


    print(f"❌ Test timed out after {TEST_TIMEOUT} seconds. No matching response received.")
    print("--- End-to-End Test Failed ---")
    r.xgroup_destroy(STREAM_OUT, consumer_group)
    exit(1)

if __name__ == "__main__":
    run_test()
