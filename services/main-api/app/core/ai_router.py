import openai

class AIRouter:
    def __init__(self, gemini_adapter, deepseek_v2_adapter, deepseek_chat_adapter, supabase_adapter):
        self.gemini_adapter = gemini_adapter
        self.deepseek_v2_adapter = deepseek_v2_adapter
        self.deepseek_chat_adapter = deepseek_chat_adapter
        self.supabase_adapter = supabase_adapter
        self.openai_client = openai.AsyncClient(api_key=os.environ.get("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-large"

    async def _get_embedding(self, text: str) -> list[float]:
        response = await self.openai_client.embeddings.create(input=[text], model=self.embedding_model)
        return response.data[0].embedding

    async def route_query(self, user_id: str, query: str, history: list, task: str, agent_prompt: str = None, agent_guardrails: str = None) -> str:
        """
        Routes a query to the appropriate AI model based on the specified task,
        implementing the 'Santo Grial' architecture with a full RAG pipeline.
        """
        # Task-based routing as per AGENT.md
        if task == 'analysis':
            print("Routing to DeepSeek-V2 for analysis.")
            return await self.deepseek_v2_adapter.generate_response(query, history)

        elif task == 'extraction':
            print("Routing to DeepSeek-Chat for data extraction.")
            return await self.deepseek_chat_adapter.generate_response(query, history)

        elif task == 'chat':
            # --- RAG Pipeline ---
            print("Initiating RAG pipeline for chat query.")
            # 1. Get embedding for the user's query
            query_embedding = await self._get_embedding(query)

            # 2. Find relevant document chunks
            relevant_chunks = self.supabase_adapter.find_relevant_chunks(user_id, query_embedding)

            context = ""
            if relevant_chunks:
                print(f"Found {len(relevant_chunks)} relevant document chunks.")
                context_texts = [chunk['content'] for chunk in relevant_chunks]
                context = "\n\n--- Relevant Information ---\n" + "\n\n".join(context_texts)
            else:
                print("No relevant document chunks found.")

            # 3. Construct the final prompt
            full_prompt = f"{agent_prompt}\n\n{context}\n\nUser Query: {query}"

            if agent_guardrails:
                full_prompt = f"Guardrails (must follow):\n{agent_guardrails}\n\n{full_prompt}"

            print("Routing to Gemini 1.5 Flash for RAG-enhanced chat.")
            return await self.gemini_adapter.generate_response(prompt=full_prompt, history=history)

        else:
            print(f"Warning: Unknown task '{task}'. Defaulting to Gemini for general chat.")
            return await self.gemini_adapter.generate_response(prompt=query, history=history)
