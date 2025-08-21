import os
from openai import AsyncOpenAI

# === Project Imports ===
# Need to use forward declaration for type hints to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.infrastructure.supabase_adapter import SupabaseAdapter
    from app.infrastructure.gemini_adapter import GeminiAdapter

# --- Configuration ---
EMBEDDING_MODEL = "text-embedding-3-large"

class OpenAIEmbeddingAdapter:
    def __init__(self, api_key: str, supabase_adapter: 'SupabaseAdapter', gemini_adapter: 'GeminiAdapter'):
        """
        Initializes the adapter with an API key and other required adapters.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Store other adapters needed for the RAG pipeline
        self.supabase_adapter = supabase_adapter
        self.gemini_adapter = gemini_adapter

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generates a vector embedding for the given text using OpenAI's API.
        """
        print(f"--- OpenAI Embeddings: Generating for text '{text[:30]}...' ---")
        try:
            text_to_embed = text.replace("\n", " ")
            response = await self.client.embeddings.create(
                input=[text_to_embed],
                model=EMBEDDING_MODEL
            )
            embedding = response.data[0].embedding
            print(f"Successfully generated embedding of dimension {len(embedding)}.")
            return embedding
        except Exception as e:
            print(f"❌ An error occurred while calling the OpenAI API: {e}")
            return []

    async def generate_response_from_rag(self, query: str) -> str:
        """
        Generates a response using a full RAG (Retrieval-Augmented Generation) pipeline.
        """
        print("--- Full RAG System ---")
        print(f"Query: {query}")

        # 1. Get embedding for the user's query
        print("Step 1: Generating embedding for the query...")
        query_embedding = await self.get_embedding(query)

        if not query_embedding:
            return "Sorry, I was unable to process your query to search the knowledge base."

        # 2. Use the embedding to search for similar documents in Supabase
        print("Step 2: Searching for relevant documents in Supabase...")
        try:
            # The similarity_search function is already in supabase_adapter
            relevant_docs = await self.supabase_adapter.similarity_search(query_embedding)
            if not relevant_docs:
                print("No relevant documents found in the knowledge base.")
                # Fallback to a direct answer if no docs are found
                return await self.gemini_adapter.generate_response(prompt=query, history=[])
        except Exception as e:
            print(f"❌ Error during similarity search: {e}")
            return "Sorry, I encountered an error while searching our knowledge base."

        print(f"Found {len(relevant_docs)} relevant document(s).")

        # 3. Construct the prompt with context and pass to Gemini
        print("Step 3: Generating final answer with LLM...")

        context_str = "\n".join([doc['content'] for doc in relevant_docs[0]])

        final_prompt = f"""
        You are a helpful AI assistant. Answer the user's query based on the following context.
        If the context does not contain the answer, say that you don't know.

        Context:
        ---
        {context_str}
        ---

        User Query: {query}
        """

        # Use the Gemini adapter for the final conversational response
        final_answer = await self.gemini_adapter.generate_response(prompt=final_prompt, history=[])

        print("RAG pipeline complete.")
        return final_answer
