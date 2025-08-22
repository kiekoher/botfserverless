import logging


logger = logging.getLogger(__name__)


class AIRouter:
    def __init__(
        self,
        gemini_adapter,
        deepseek_v2_adapter,
        deepseek_chat_adapter,
        openai_embedding_adapter,
    ):
        self.gemini_adapter = gemini_adapter
        self.deepseek_v2_adapter = deepseek_v2_adapter
        self.deepseek_chat_adapter = deepseek_chat_adapter
        self.openai_embedding_adapter = openai_embedding_adapter
        # Reuse Supabase adapter from the embedding adapter for RAG searches
        self.supabase_adapter = openai_embedding_adapter.supabase_adapter

    async def _get_embedding(self, text: str) -> list[float]:
        return await self.openai_embedding_adapter.get_embedding(text)

    async def route_query(self, user_id: str, query: str, history: list, task: str, agent_prompt: str = None, agent_guardrails: str = None) -> str:
        """
        Routes a query to the appropriate AI model based on the specified task,
        implementing the 'Santo Grial' architecture with a full RAG pipeline.
        """
        # Task-based routing as per AGENT.md
        if task == 'analysis':
            logger.info("Routing to DeepSeek-V2 for analysis.")
            return await self.deepseek_v2_adapter.generate_response(query, history)

        elif task == 'extraction':
            logger.info("Routing to DeepSeek-Chat for data extraction.")
            return await self.deepseek_chat_adapter.generate_response(query, history)

        elif task == 'chat':
            # --- RAG Pipeline ---
            logger.info("Initiating RAG pipeline for chat query.")
            # 1. Get embedding for the user's query
            query_embedding = await self._get_embedding(query)

            # 2. Find relevant document chunks
            relevant_chunks = self.supabase_adapter.find_relevant_chunks(user_id, query_embedding)

            context = ""
            if relevant_chunks:
                logger.info("Found %d relevant document chunks.", len(relevant_chunks))
                context_texts = [chunk['content'] for chunk in relevant_chunks]
                context = "\n\n--- Relevant Information ---\n" + "\n\n".join(context_texts)
            else:
                logger.info("No relevant document chunks found.")

            # 3. Construct the final prompt
            full_prompt = f"{agent_prompt}\n\n{context}\n\nUser Query: {query}"

            if agent_guardrails:
                full_prompt = f"Guardrails (must follow):\n{agent_guardrails}\n\n{full_prompt}"

            logger.info("Routing to Gemini 1.5 Flash for RAG-enhanced chat.")
            return await self.gemini_adapter.generate_response(prompt=full_prompt, history=history)

        else:
            logger.warning("Unknown task '%s'. Defaulting to Gemini for general chat.", task)
            return await self.gemini_adapter.generate_response(prompt=query, history=history)
