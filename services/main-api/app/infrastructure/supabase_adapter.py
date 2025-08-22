import os
import logging
from supabase import create_client, Client


logger = logging.getLogger(__name__)


class SupabaseAdapter:
    def __init__(self, url: str | None = None, key: str | None = None):
        url = url or os.getenv("SUPABASE_URL")
        key = key or os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment."
            )
        self.client: Client = create_client(url, key)

    def get_agent_for_user(self, user_id: str):
        """
        Retrieves the first agent associated with a user.
        NOTE: This is a simplification. A real app would have a more robust
        way to select the correct agent.
        """
        try:
            response = self.client.table("agents").select("*").eq("user_id", user_id).limit(1).single().execute()
            return response.data
        except Exception as e:
            logger.error("Error fetching agent for user %s: %s", user_id, e)
            return None

    def list_agents_for_user(self, user_id: str):
        """Return all agents belonging to a user."""
        try:
            response = (
                self.client.table("agents")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error("Error listing agents for user %s: %s", user_id, e)
            return []

    def upsert_agent_config(self, user_id: str, name: str, product_description: str, base_prompt: str):
        """
        Creates or updates an agent's configuration.
        An upsert is used to ensure a user has only one agent entry.
        """
        try:
            # The 'on_conflict' parameter is not directly supported in supabase-py v1.
            # We must use an RPC call for this or do a select-then-insert/update.
            # For simplicity, we'll use upsert which is available in v2 or do it manually.
            # Let's check for an existing agent first.
            existing_agent = self.client.table("agents").select("id").eq("user_id", user_id).limit(1).single().execute()

            agent_data = {
                "user_id": user_id,
                "name": name,
                "product_description": product_description,
                "base_prompt": base_prompt,
                "status": "active"
            }

            if existing_agent.data:
                # Update existing agent
                response = self.client.table("agents").update(agent_data).eq("user_id", user_id).execute()
            else:
                # Insert new agent
                response = self.client.table("agents").insert(agent_data).execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error upserting agent for user %s: %s", user_id, e)
            return None

    def create_document_record(self, user_id: str, agent_id: str, file_name: str, storage_path: str):
        """
        Creates a new record in the 'documents' table.
        """
        try:
            response = self.client.table("documents").insert({
                "user_id": user_id,
                "agent_id": agent_id,
                "file_name": file_name,
                "storage_path": storage_path,
                "status": "pending"
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error creating document record for user %s: %s", user_id, e)
            return None

    def get_documents_for_user(self, user_id: str):
        """
        Retrieves all document records for a given user.
        """
        try:
            response = self.client.table("documents").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error("Error fetching documents for user %s: %s", user_id, e)
            return []

    def get_conversation_history(self, agent_id: str, user_id: str, limit: int = 10):
        """
        Retrieves the last N conversation turns for a given agent and user.
        """
        try:
            response = self.client.table("conversations") \
                .select("user_message, bot_response, created_at") \
                .eq("agent_id", agent_id) \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

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

    def log_conversation(
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
            data, count = (
                self.client.table("conversations")
                .insert(
                    {
                        "agent_id": agent_id,
                        "user_id": user_id,
                        "user_message": user_message,
                        "bot_response": bot_response,
                    }
                )
                .execute()
            )
            return data
        except Exception as e:
            logger.error("Error logging conversation to Supabase: %s", e)
            return None

    def get_embeddings(self, text: str):
        """
        Placeholder for getting embeddings. This might be done via a different service
        or a Supabase edge function.
        """
        # In a real scenario, this might call a Supabase edge function
        # or another embedding service.
        pass

    def find_relevant_chunks(
        self, user_id: str, query_embedding: list[float], match_threshold: float = 0.5, match_count: int = 5
    ):
        """
        Performs a similarity search on the 'document_chunks' table for a specific user.
        """
        try:
            response = self.client.rpc(
                "match_document_chunks",
                {
                    "p_user_id": user_id,
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count,
                },
            ).execute()
            return response.data
        except Exception as e:
            logger.error("Error performing similarity search in Supabase: %s", e)
            return []

    def delete_document(self, document_id: str) -> bool:
        """Deletes a document record by id."""
        try:
            self.client.table("documents").delete().eq("id", document_id).execute()
            return True
        except Exception as e:
            logger.error("Error deleting document %s: %s", document_id, e)
            return False
