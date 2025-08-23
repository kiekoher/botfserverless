import asyncio
import logging
import os
from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{REDIS_HOST}:6379"
DLQ_STREAM = "events:dead_letter_queue"
CONSUMER_GROUP = "group:dlq-monitor"
CONSUMER_NAME = f"consumer:dlq-monitor-{os.getpid()}"

async def setup(redis: Redis):
    try:
        await redis.xgroup_create(DLQ_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info("Consumer group '%s' created", CONSUMER_GROUP)
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info("Consumer group '%s' already exists", CONSUMER_GROUP)
        else:
            raise

import json

async def handle_messages(redis: Redis):
    logger.info("Listening for DLQ messages on stream '%s'", DLQ_STREAM)
    while True:
        try:
            response = await redis.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {DLQ_STREAM: ">"}, count=10, block=5000
            )
            if not response:
                continue

            for _, messages in response:
                for message_id, message_data in messages:
                    # Log as a structured JSON for better parsing and alerting
                    log_payload = {
                        "alert": "DeadLetterQueueMessageReceived",
                        "stream": DLQ_STREAM,
                        "message_id": message_id,
                        "service_name": message_data.get("error_service", "unknown"),
                        "payload": message_data
                    }
                    logger.critical(json.dumps(log_payload))

                    # Acknowledge the message so it's not processed again
                    await redis.xack(DLQ_STREAM, CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.error("Error in DLQ monitor loop: %s", e)
            await asyncio.sleep(5) # Wait before retrying in case of connection issues

async def main():
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    await setup(redis)
    await handle_messages(redis)

if __name__ == "__main__":
    asyncio.run(main())
