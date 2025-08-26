import json
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from app.dependencies import get_redis

router = APIRouter()

DLQ_LIST_KEY = "dlq:persistent_failures"
REPROCESSING_STREAM = "events:new_message"

@router.get("/dlq", status_code=status.HTTP_200_OK)
async def get_dlq_messages(redis: Redis = Depends(get_redis)):
    """
    Retrieves all messages from the Dead Letter Queue persistent list.
    """
    try:
        # Get all items from the list
        messages_str = await redis.lrange(DLQ_LIST_KEY, 0, -1)
        # Decode each JSON string message
        messages = [json.loads(msg) for msg in messages_str]
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve DLQ messages: {e}",
        )

@router.post("/dlq/reprocess", status_code=status.HTTP_200_OK)
async def reprocess_dlq_message(message: dict, redis: Redis = Depends(get_redis)):
    """
    Reprocesses a message from the DLQ by moving it to the main processing stream.
    """
    message_str = json.dumps(message)
    try:
        # Re-queue the original message data for processing
        await redis.xadd(REPROCESSING_STREAM, message["data"])
        # Remove the message from the DLQ list
        removed_count = await redis.lrem(DLQ_LIST_KEY, 1, message_str)
        if removed_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in DLQ list. It might have been reprocessed already.",
            )
        return {"status": "ok", "detail": "Message re-queued for processing."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess message: {e}",
        )

@router.delete("/dlq/item", status_code=status.HTTP_200_OK)
async def delete_dlq_message(message: dict, redis: Redis = Depends(get_redis)):
    """
    Deletes a message from the DLQ list without reprocessing it.
    """
    message_str = json.dumps(message)
    try:
        removed_count = await redis.lrem(DLQ_LIST_KEY, 1, message_str)
        if removed_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in DLQ list.",
            )
        return {"status": "ok", "detail": "Message deleted from DLQ."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {e}",
        )
