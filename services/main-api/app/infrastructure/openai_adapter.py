import os
import logging
from openai import AsyncOpenAI

# === Project Imports ===
# Need to use forward declaration for type hints to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.infrastructure.supabase_adapter import SupabaseAdapter
    from app.infrastructure.gemini_adapter import GeminiAdapter

# --- Configuration ---
EMBEDDING_MODEL = "text-embedding-3-large"

logger = logging.getLogger(__name__)

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
        logger.info("OpenAI Embeddings: generating for text '%s'...", text[:30])
        try:
            text_to_embed = text.replace("\n", " ")
            response = await self.client.embeddings.create(
                input=[text_to_embed],
                model=EMBEDDING_MODEL
            )
            embedding = response.data[0].embedding
            logger.info(
                "Successfully generated embedding of dimension %d.",
                len(embedding),
            )
            return embedding
        except Exception as e:
            logger.error("An error occurred while calling the OpenAI API: %s", e)
            return []

    async def generate_response_from_rag(self, query: str, user_id: str) -> str:
        """
        Generates a response using a full RAG (Retrieval-Augmented Generation) pipeline.
        """
        logger.info("Full RAG System for query: %s", query)

        # 1. Get embedding for the user's query
        logger.info("Step 1: Generating embedding for the query...")
        query_embedding = await self.get_embedding(query)

        if not query_embedding:
            return "Sorry, I was unable to process your query to search the knowledge base."

        # 2. Use the embedding to search for similar documents in Supabase
        logger.info("Step 2: Searching for relevant documents in Supabase...")
        try:
            relevant_docs = await self.supabase_adapter.find_relevant_chunks(
                user_id, query_embedding
            )
            if not relevant_docs:
                logger.info("No relevant documents found in the knowledge base.")
                return await self.gemini_adapter.generate_response(
                    prompt=query, history=[]
                )
        except Exception as e:
            logger.error("Error during similarity search: %s", e)
            return "Sorry, I encountered an error while searching our knowledge base."

        logger.info("Found %d relevant document(s).", len(relevant_docs))

        # 3. Construct the prompt with context and pass to Gemini
        logger.info("Step 3: Generating final answer with LLM...")

        context_str = "\n".join([doc['content'] for doc in relevant_docs])

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

        logger.info("RAG pipeline complete.")
        return final_answer
