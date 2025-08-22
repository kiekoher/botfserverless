class AIRouter:
    def __init__(self, gemini_adapter, deepseek_v2_adapter, deepseek_chat_adapter, openai_embedding_adapter):
        self.gemini_adapter = gemini_adapter
        self.deepseek_v2_adapter = deepseek_v2_adapter
        self.deepseek_chat_adapter = deepseek_chat_adapter
        self.openai_embedding_adapter = openai_embedding_adapter

    async def route_query(self, query: str, history: list, task: str, agent_prompt: str = None, agent_guardrails: str = None) -> str:
        """
        Routes a query to the appropriate AI model based on the specified task,
        implementing the 'Santo Grial' architecture.
        """
        full_prompt = query
        if agent_prompt:
            full_prompt = f"Base Instructions: {agent_prompt}\n\nUser Query: {query}"

        if agent_guardrails:
            # A real implementation would have a more sophisticated guardrail system.
            # For now, we prepend them as a system instruction.
            full_prompt = f"Guardrails (must follow):\n{agent_guardrails}\n\n{full_prompt}"

        # Task-based routing as per AGENT.md
        if task == 'analysis':
            print("Routing to DeepSeek-V2 for analysis.")
            return await self.deepseek_v2_adapter.generate_response(full_prompt, history)
        elif task == 'extraction':
            print("Routing to DeepSeek-Chat for data extraction.")
            return await self.deepseek_chat_adapter.generate_response(full_prompt, history)
        elif task == 'chat':
            # NOTE: RAG logic will be properly integrated in the next step.
            # For now, simple question detection remains.
            if "?" in query:
                print("Routing to RAG (OpenAI Embeddings) for question answering.")
                # The RAG response generation is still partially simulated.
                return await self.openai_embedding_adapter.generate_response_from_rag(query)

            print("Routing to Gemini 1.5 Flash for general chat.")
            return await self.gemini_adapter.generate_response(prompt=full_prompt, history=history)
        else:
            print(f"Warning: Unknown task '{task}'. Defaulting to Gemini for general chat.")
            return await self.gemini_adapter.generate_response(prompt=full_prompt, history=history)
