import os
import redis
import time
import asyncio
from app.core.use_cases.process_chat_message import ProcessChatMessage
from app.infrastructure.gemini_adapter import GeminiAdapter
from app.infrastructure.supabase_adapter import SupabaseAdapter
from app.core.ai_router import AIRouter
from app.infrastructure.deepseek_adapter import DeepSeekV2Adapter, DeepSeekChatAdapter
from app.infrastructure.openai_adapter import OpenAIEmbeddingAdapter

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
STREAM_IN = "events:transcribed_message"
STREAM_OUT = "events:message_out"
CONSUMER_GROUP = "group:main-api"
CONSUMER_NAME = "consumer:main-api-1"

print("🤖 Main API Worker starting...")

# Initialize dependencies manually
print("🔌 Initializing adapters...")
supabase_adapter = SupabaseAdapter()
gemini_adapter = GeminiAdapter()
deepseek_v2_adapter = DeepSeekV2Adapter(api_key=os.getenv("DEEPSEEK_API_KEY"))
deepseek_chat_adapter = DeepSeekChatAdapter(api_key=os.getenv("DEEPSEEK_API_KEY"))
openai_embedding_adapter = OpenAIEmbeddingAdapter(api_key=os.getenv("OPENAI_API_KEY"))
print("✅ Adapters initialized.")

# Initialize the AI Router
print("🧠 Initializing AI Router...")
ai_router = AIRouter(
    gemini_adapter=gemini_adapter,
    deepseek_v2_adapter=deepseek_v2_adapter,
    deepseek_chat_adapter=deepseek_chat_adapter,
    openai_embedding_adapter=openai_embedding_adapter,
)
print("✅ AI Router initialized.")

# Initialize the main use case
process_chat_message_use_case = ProcessChatMessage(
    router=ai_router, db_adapter=supabase_adapter
)

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


def setup_redis():
    """Create consumer group if it doesn't exist."""
    try:
        r.xgroup_create(STREAM_IN, CONSUMER_GROUP, id="0", mkstream=True)
        print(f"Consumer group '{CONSUMER_GROUP}' created.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{CONSUMER_GROUP}' already exists.")
        else:
            print(f"Error setting up Redis group: {e}")
            raise


# Dead Letter Queue configuration
# After MAX_RETRIES failures the message is moved to DEAD_LETTER_QUEUE
DEAD_LETTER_QUEUE = "events:dead_letter_queue"
MAX_RETRIES = 3


async def process_message_with_retry(message_id, message_data):
    """Process a message with a retry mechanism."""
    for attempt in range(MAX_RETRIES):
        try:
            print(
                f"Processing message {message_id}, attempt {attempt + 1}/{MAX_RETRIES}"
            )
            user_id = message_data.get("userId")
            query = message_data.get("body")

            if not user_id or not query:
                print("Message missing userId or body, skipping.")
                return True  # Acknowledge and move on

            # Execute the use case
            bot_response_text = await process_chat_message_use_case.execute(
                user_id=user_id, user_query=query
            )

            # Prepare the output payload
            output_payload = {"userId": user_id, "body": bot_response_text}

            # Publish the response
            r.xadd(STREAM_OUT, output_payload)
            print(f"Published response for {user_id} to {STREAM_OUT}")
            return True  # Success

        except Exception as e:
            print(
                f"Error processing message {message_id} on attempt {attempt + 1}: {e}"
            )
            if attempt + 1 == MAX_RETRIES:
                print(
                    f"Message {message_id} failed after {MAX_RETRIES} attempts. Moving to DLQ."
                )
                return False  # Failure
            await asyncio.sleep(2**attempt)  # Exponential backoff

    return False


async def main_loop():
    """The main worker loop."""
    print("👂 Starting to listen for messages...")
    while True:
        try:
            response = r.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {STREAM_IN: ">"}, count=1, block=5000
            )

            if not response:
                continue

            for stream, messages in response:
                for message_id, message_data in messages:
                    print(f"Received message {message_id}: {message_data}")

                    success = await process_message_with_retry(message_id, message_data)

                    if success:
                        r.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        print(
                            f"Successfully processed and acknowledged message {message_id}"
                        )
                    else:
                        # Move to DLQ
                        dlq_payload = message_data.copy()
                        dlq_payload["error_service"] = "main-api"
                        dlq_payload["error_timestamp"] = time.time()
                        r.xadd(DEAD_LETTER_QUEUE, dlq_payload)
                        r.xack(
                            STREAM_IN, CONSUMER_GROUP, message_id
                        )  # Ack original message
                        print(
                            f"Moved message {message_id} to DLQ '{DEAD_LETTER_QUEUE}'"
                        )

        except Exception as e:
            print(f"A critical error occurred in main loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    setup_redis()
    asyncio.run(main_loop())
