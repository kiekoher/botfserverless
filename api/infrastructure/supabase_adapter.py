import os
import asyncio
import logging
from supabase import create_client, Client


logger = logging.getLogger(__name__)


class SupabaseAdapter:
    def __init__(self, url: str | None = None, key: str | None = None):
        url = url or os.getenv("SUPABASE_URL")
        key = key or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment."
            )
        self.client: Client = create_client(url, key)
    async def _execute(self, query):
        return await asyncio.to_thread(query.execute)

    async def get_agent_for_user(self, user_id: str):
        """
        Retrieves the first agent associated with a user.
        NOTE: This is a simplification. A real app would have a more robust
        way to select the correct agent.
        """
        try:
            query = (
                self.client.table("agents")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .single()
            )
            response = await self._execute(query)

            agent_data = response.data
            if agent_data and "config" in agent_data:
                # Unpack the config dict into the main dict
                config_data = agent_data.pop("config")
                agent_data.update(config_data)

            return agent_data
        except Exception as e:
            logger.error("Error fetching agent for user %s: %s", user_id, e)
            return None

    async def list_agents_for_user(self, user_id: str):
        """Return all agents belonging to a user."""
        try:
            query = (
                self.client.table("agents")
                .select("*")
                .eq("user_id", user_id)
            )
            response = await self._execute(query)
            return response.data
        except Exception as e:
            logger.error("Error listing agents for user %s: %s", user_id, e)
            return []

    async def upsert_agent_config(self, user_id: str, name: str, product_description: str, base_prompt: str):
        """
        Creates or updates an agent's configuration.
        An upsert is used to ensure a user has only one agent entry.
        """
        try:
            # The 'on_conflict' parameter is not directly supported in supabase-py v1.
            # We must use an RPC call for this or do a select-then-insert/update.
            # For simplicity, we'll use upsert which is available in v2 or do it manually.
            # Let's check for an existing agent first.
            existing_query = (
                self.client.table("agents")
                .select("id")
                .eq("user_id", user_id)
                .limit(1)
                .single()
            )
            existing_agent = await self._execute(existing_query)

            # This dictionary must match the table schema.
            # 'product_description' goes into the 'config' JSONB field.
            agent_data = {
                "user_id": user_id,
                "name": name,
                "base_prompt": base_prompt,
                "status": "active",
                "config": {
                    "product_description": product_description
                }
            }

            if existing_agent.data:
                # Update existing agent
                agent_id = existing_agent.data['id']
                response = await self._execute(
                    self.client.table("agents").update(agent_data).eq("id", agent_id)
                )
            else:
                # Insert new agent
                response = await self._execute(
                    self.client.table("agents").insert(agent_data)
                )

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error upserting agent for user %s: %s", user_id, e)
            return None

    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Updates the status field for a given agent."""
        try:
            query = (
                self.client.table("agents")
                .update({"status": status})
                .eq("id", agent_id)
            )
            await self._execute(query)
            return True
        except Exception as e:
            logger.error("Error updating status for agent %s: %s", agent_id, e)
            return False

    async def create_document_record(self, user_id: str, agent_id: str, file_name: str, storage_path: str):
        """
        Creates a new record in the 'documents' table.
        """
        try:
            query = self.client.table("documents").insert({
                "user_id": user_id,
                "agent_id": agent_id,
                "file_name": file_name,
                "storage_path": storage_path,
                "status": "pending"
            })
            response = await self._execute(query)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error creating document record for user %s: %s", user_id, e)
            return None

    async def get_documents_for_user(self, user_id: str):
        """
        Retrieves all document records for a given user.
        """
        try:
            query = (
                self.client.table("documents")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
            )
            response = await self._execute(query)
            return response.data
        except Exception as e:
            logger.error("Error fetching documents for user %s: %s", user_id, e)
            return []

    async def get_conversation_history(self, agent_id: str, user_id: str, limit: int = 10):
        """
        Retrieves the last N conversation turns for a given agent and user.
        """
        try:
            query = (
                self.client.table("conversations")
                .select("user_message, bot_response, created_at")
                .eq("agent_id", agent_id)
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
            )
            response = await self._execute(query)

            # The history needs to be in chronological order for the AI
            history = sorted(response.data, key=lambda x: x['created_at'])

            # Format for AI model (e.g., Gemini)
            formatted_history = []
            for turn in history:
                formatted_history.append({"role": "user", "parts": [{"text": turn["user_message"]}]})
                formatted_history.append({"role": "model", "parts": [{"text": turn["bot_response"]}]})

            return formatted_history
        except Exception as e:
            logger.error("Error fetching conversation history for agent %s: %s", agent_id, e)
            return []

    async def log_conversation(
        self,
        agent_id: str,
        user_id: str,
        user_message: str,
        bot_response: str,
    ):
        """
        Logs a conversation to the 'conversations' table in Supabase.
        """
        try:
            query = self.client.table("conversations").insert(
                {
                    "agent_id": agent_id,
                    "user_id": user_id,
                    "user_message": user_message,
                    "bot_response": bot_response,
                }
            )
            data = await self._execute(query)
            return data
        except Exception as e:
            logger.error("Error logging conversation to Supabase: %s", e)
            return None

    async def find_relevant_chunks(
        self, user_id: str, query_embedding: list[float], match_threshold: float = 0.5, match_count: int = 5
    ):
        """
        Performs a similarity search on the 'document_chunks' table for a specific user.
        """
        try:
            query = self.client.rpc(
                "match_document_chunks",
                {
                    "p_user_id": user_id,
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count,
                },
            )
            response = await self._execute(query)
            return response.data
        except Exception as e:
            logger.error("Error performing similarity search in Supabase: %s", e)
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Deletes a document record by id."""
        try:
            query = self.client.table("documents").delete().eq("id", document_id)
            await self._execute(query)
            return True
        except Exception as e:
            logger.error("Error deleting document %s: %s", document_id, e)
            return False

    # === Billing and Subscription Methods ===

    async def get_stripe_customer_id(self, user_id: str) -> str | None:
        """Retrieves the Stripe customer ID for a given user."""
        try:
            query = self.client.table("subscriptions").select("stripe_customer_id").eq("user_id", user_id).limit(1).single()
            response = await self._execute(query)
            return response.data.get("stripe_customer_id") if response.data else None
        except Exception: # Catches PostgrestError when no rows are found
            return None

    async def get_user_by_stripe_customer_id(self, customer_id: str):
        """Finds a user by their Stripe customer ID."""
        try:
            query = self.client.table("subscriptions").select("user_id").eq("stripe_customer_id", customer_id).limit(1).single()
            response = await self._execute(query)
            return response.data
        except Exception as e:
            logger.error(f"Error getting user by stripe_customer_id {customer_id}: {e}")
            return None

    async def get_subscription_for_user(self, user_id: str):
        """Retrieves the subscription details for a user."""
        try:
            query = self.client.table("subscriptions").select("*, plans(*)").eq("user_id", user_id).order("created_at", desc=True).limit(1).single()
            response = await self._execute(query)
            return response.data
        except Exception:
            return None

    async def create_subscription(self, user_id: str, plan_id: str, status: str, stripe_subscription_id: str, stripe_customer_id: str, current_period_start: str, current_period_end: str, cancel_at_period_end: bool):
        """Creates or updates a subscription record for a user."""
        try:
            # Upsert logic: update if subscription exists, otherwise insert.
            query = self.client.table("subscriptions").upsert({
                "user_id": user_id,
                "plan_id": plan_id,
                "status": status,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "cancel_at_period_end": cancel_at_period_end,
            }, on_conflict="stripe_subscription_id")
            response = await self._execute(query)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating/updating subscription for user {user_id}: {e}")
            return None

    async def update_subscription_status(self, stripe_subscription_id: str, new_status: str, cancel_at_period_end: bool, current_period_start: str = None, current_period_end: str = None):
        """Updates a subscription based on a webhook event."""
        try:
            update_data = {
                "status": new_status,
                "cancel_at_period_end": cancel_at_period_end,
            }
            if current_period_start:
                update_data["current_period_start"] = current_period_start
            if current_period_end:
                update_data["current_period_end"] = current_period_end

            query = self.client.table("subscriptions").update(update_data).eq("stripe_subscription_id", stripe_subscription_id)
            response = await self._execute(query)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating subscription {stripe_subscription_id}: {e}")
            return None

    async def get_quality_metrics(self, user_id: str):
        """Fetch quality metrics for a user."""
        try:
            query = (
                self.client.table("quality_metrics")
                .select("conversations_reviewed, avg_response_time_sec, csat")
                .eq("user_id", user_id)
                .limit(1)
                .single()
            )
            response = await self._execute(query)
            data = response.data or {}
        except Exception as e:
            logger.error("Error fetching quality metrics for user %s: %s", user_id, e)
            data = {}
        return {
            "user_id": user_id,
            "conversations_reviewed": data.get("conversations_reviewed", 0),
            "avg_response_time_sec": data.get("avg_response_time_sec", 0),
            "csat": data.get("csat", 0.0),
        }

    async def get_opportunity_briefs(self, user_id: str):
        """Fetch opportunity briefs for a user."""
        try:
            query = (
                self.client.table("opportunity_briefs")
                .select("*")
                .eq("user_id", user_id)
            )
            response = await self._execute(query)
            data = response.data or []
        except Exception as e:
            logger.error("Error fetching opportunity briefs for user %s: %s", user_id, e)
            data = []
        return {"user_id": user_id, "opportunities": data}

    async def get_performance_log(self, user_id: str):
        """Fetch performance logs for a user."""
        try:
            query = (
                self.client.table("performance_logs")
                .select("*")
                .eq("user_id", user_id)
            )
            response = await self._execute(query)
            data = response.data or []
        except Exception as e:
            logger.error("Error fetching performance log for user %s: %s", user_id, e)
            data = []
        return {"user_id": user_id, "logs": data}

    async def get_executive_summaries(self, user_id: str):
        """Fetch executive summaries for a user."""
        try:
            query = (
                self.client.table("executive_summaries")
                .select("*")
                .eq("user_id", user_id)
            )
            response = await self._execute(query)
            data = response.data or []
        except Exception as e:
            logger.error("Error fetching executive summaries for user %s: %s", user_id, e)
            data = []
        return {"user_id": user_id, "summaries": data}
