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

async def handle_messages(redis: Redis):
    logger.info("Listening for DLQ messages...")
    while True:
        response = await redis.xreadgroup(
            CONSUMER_GROUP, CONSUMER_NAME, {DLQ_STREAM: ">"}, count=1, block=5000
        )
        if not response:
            continue
        for _, messages in response:
            for message_id, message_data in messages:
                logger.error("DLQ message %s: %s", message_id, message_data)
                # Placeholder for alerting/metrics integration
                await redis.xack(DLQ_STREAM, CONSUMER_GROUP, message_id)

async def main():
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    await setup(redis)
    await handle_messages(redis)

if __name__ == "__main__":
    asyncio.run(main())
