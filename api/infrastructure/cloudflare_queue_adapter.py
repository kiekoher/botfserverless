import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CloudflareQueueAdapter:
    def __init__(
        self, account_id: str, api_token: str, queue_id: str, http_client: httpx.AsyncClient
    ):
        self.account_id = account_id
        self.api_token = api_token
        self.queue_id = queue_id
        self.http_client = http_client
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/queues/{self.queue_id}/messages"

    async def publish_message(self, payload: Dict[str, Any]):
        """
        Publishes a message to the configured Cloudflare Queue.
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        # Cloudflare Queues expects a list of messages
        data = {"messages": [{"body": payload}]}

        try:
            logger.info(f"Publishing message to Cloudflare Queue '{self.queue_id}'...")
            response = await self.http_client.post(
                self.base_url,
                json=data,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            logger.info(f"Successfully published message to queue. Response: {response.json()}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred while publishing to Cloudflare Queue: {e.response.status_code} - {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while publishing to Cloudflare Queue: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise
