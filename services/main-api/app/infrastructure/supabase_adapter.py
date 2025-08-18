import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseAdapter:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
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
            print(f"Error fetching agent for user {user_id}: {e}")
            return None

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
            print(f"Error logging conversation to Supabase: {e}")
            return None

    def get_embeddings(self, text: str):
        """
        Placeholder for getting embeddings. This might be done via a different service
        or a Supabase edge function.
        """
        # In a real scenario, this might call a Supabase edge function
        # or another embedding service.
        pass

    def similarity_search(
        self, query_embedding, match_threshold: float = 0.78, match_count: int = 5
    ):
        """
        Performs a similarity search on the 'documents' table.
        """
        try:
            data, count = self.client.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count,
                },
            ).execute()
            return data
        except Exception as e:
            print(f"Error performing similarity search in Supabase: {e}")
            return None
