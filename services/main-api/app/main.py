import os
import redis
import time
import asyncio
from app.core.use_cases.process_chat_message import ProcessChatMessage
from app.dependencies import get_process_chat_message_use_case # I'll need to check this dependency
from app.infrastructure.gemini_adapter import GeminiAdapter
from app.infrastructure.supabase_adapter import SupabaseAdapter

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
STREAM_IN = "events:transcribed_message"
STREAM_OUT = "events:message_out"
CONSUMER_GROUP = "group:main-api"
CONSUMER_NAME = "consumer:main-api-1"

print("🤖 Main API Worker starting...")

from app.core.ai_router import AIRouter
from app.infrastructure.deepseek_adapter import DeepSeekV2Adapter, DeepSeekChatAdapter
from app.infrastructure.openai_adapter import OpenAIEmbeddingAdapter

# Initialize dependencies manually
print("🔌 Initializing adapters...")
supabase_adapter = SupabaseAdapter(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_KEY")
)
gemini_adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))
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
    openai_embedding_adapter=openai_embedding_adapter
)
print("✅ AI Router initialized.")

# Initialize the main use case
process_chat_message_use_case = ProcessChatMessage(
    router=ai_router,
    db_adapter=supabase_adapter
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

async def main_loop():
    """The main worker loop."""
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

                    user_id = message_data.get('userId')
                    query = message_data.get('body')

                    if not user_id or not query:
                        print("Message missing userId or body, skipping.")
                        r.xack(STREAM_IN, CONSUMER_GROUP, message_id)
                        continue

                    # Execute the use case
                    # For now, we pass an empty history. This will be managed by the use case.
                    bot_response_text = await process_chat_message_use_case.execute(
                        user_id=user_id,
                        user_query=query,
                        history=[]
                    )

                    # Prepare the output payload
                    output_payload = {
                        'userId': user_id,
                        'body': bot_response_text
                    }

                    # Publish the response
                    r.xadd(STREAM_OUT, output_payload)
                    print(f"Published response for {user_id} to {STREAM_OUT}")

                    # Acknowledge the message
                    r.xack(STREAM_IN, CONSUMER_GROUP, message_id)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)

if __name__ == "__main__":
    setup_redis()
    asyncio.run(main_loop())
