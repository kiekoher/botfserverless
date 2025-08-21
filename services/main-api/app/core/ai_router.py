class AIRouter:
    def __init__(self, gemini_adapter, deepseek_v2_adapter, deepseek_chat_adapter, openai_embedding_adapter):
        self.gemini_adapter = gemini_adapter
        self.deepseek_v2_adapter = deepseek_v2_adapter
        self.deepseek_chat_adapter = deepseek_chat_adapter
        self.openai_embedding_adapter = openai_embedding_adapter

    async def route_query(self, query: str, history: list, agent_prompt: str = None, agent_guardrails: str = None) -> str:
        """
        Determines which AI model to use based on the query and agent configuration.
        """

        full_prompt = query
        if agent_prompt:
            full_prompt = f"Base Instructions: {agent_prompt}\n\nUser Query: {query}"

        if agent_guardrails:
            # A real implementation would have a more sophisticated guardrail system.
            # For now, we prepend them as a system instruction.
            full_prompt = f"Guardrails (must follow):\n{agent_guardrails}\n\n{full_prompt}"


        # Simple keyword-based routing
        if "analizar" in query.lower():
            print("Routing to DeepSeek-V2 for analysis.")
            return await self.deepseek_v2_adapter.generate_response(full_prompt, history)
        elif "extraer" in query.lower():
            print("Routing to DeepSeek-Chat for data extraction.")
            return await self.deepseek_chat_adapter.generate_response(full_prompt, history)
        elif "?" in query:
            print("Routing to RAG (OpenAI Embeddings) for question answering.")
            # The RAG response generation is still partially simulated, but the call is real.
            return await self.openai_embedding_adapter.generate_response_from_rag(query)
        else:
            print("Routing to Gemini for general chat.")
            return await self.gemini_adapter.generate_response(prompt=full_prompt, history=history)
