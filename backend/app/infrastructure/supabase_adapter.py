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

    def log_conversation(
        self,
        user_id: str,
        user_query: str,
        bot_response: str,
        context_chunks: list[str],
    ):
        """
        Logs a conversation to the 'conversations' table in Supabase.
        """
        try:
            data, count = (
                self.client.table("conversations")
                .insert(
                    {
                        "user_id": user_id,
                        "user_message": user_query,
                        "bot_response": bot_response,
                        "retrieved_context": context_chunks,
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
