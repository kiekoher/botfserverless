import asyncio
import logging
import os
import json
from redis.asyncio import Redis
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{REDIS_HOST}:6379"
DLQ_STREAM = "events:dead_letter_queue"
DLQ_PERSISTENT_LIST = "dlq:persistent_failures"
CONSUMER_GROUP = "group:dlq-monitor"
CONSUMER_NAME = f"consumer:dlq-monitor-{os.getpid()}"

HEALTHCHECK_FILE = Path("/tmp/health/last_processed")

async def touch_healthcheck_file():
    """Updates the modification time of the healthcheck file."""
    try:
        HEALTHCHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEALTHCHECK_FILE.touch()
    except Exception as e:
        logger.warning("Could not touch healthcheck file: %s", e)

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
    logger.info("Listening for DLQ messages on stream '%s'", DLQ_STREAM)
    while True:
        try:
            # Signal that the worker is alive and polling
            await touch_healthcheck_file()

            response = await redis.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {DLQ_STREAM: ">"}, count=10, block=5000
            )
            if not response:
                continue

            for _, messages in response:
                for message_id, message_data in messages:
                    # Persist the failed message to a simple list for reprocessing
                    message_to_persist = {
                        "message_id": message_id,
                        "data": message_data,
                    }
                    await redis.lpush(DLQ_PERSISTENT_LIST, json.dumps(message_to_persist))

                    # Log that the message has been persisted for manual review
                    log_payload = {
                        "alert": "DeadLetterQueueMessagePersisted",
                        "stream": DLQ_STREAM,
                        "message_id": message_id,
                        "service_name": message_data.get("error_service", "unknown"),
                        "action": f"Message persisted to list '{DLQ_PERSISTENT_LIST}' for reprocessing."
                    }
                    logger.critical(json.dumps(log_payload))

                    # Acknowledge the message so it's removed from the DLQ stream
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
