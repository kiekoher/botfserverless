from app.infrastructure.gemini_adapter import GeminiAdapter
from app.infrastructure.supabase_adapter import SupabaseAdapter


class ProcessChatMessage:
    def __init__(
        self, supabase_adapter: SupabaseAdapter, gemini_adapter: GeminiAdapter
    ):
        self.supabase_adapter = supabase_adapter
        self.gemini_adapter = gemini_adapter

    async def execute(self, user_id: str, user_query: str, history: list) -> str:
        """
        Orchestrates the processing of a user's chat message.
        """
        # 1. Classify intent
        classification = await self.gemini_adapter.classify_and_extract(user_query)

        bot_response = ""
        context_chunks = []

        # 2. Execute based on intent
        if classification.get("decision") == "use_rag":
            summary = classification.get("summary_for_rag", user_query)

            # Get query embedding
            query_embedding = await self.gemini_adapter.get_embedding(summary)

            # Search for similar documents in Supabase
            context_chunks = self.supabase_adapter.similarity_search(query_embedding)

            # Generate response using RAG
            bot_response = await self.gemini_adapter.generate_rag_response(
                query=summary, context=context_chunks, history=history
            )

        elif classification.get("decision") == "use_tool":
            tool_call = classification.get("tool_call", {})
            if tool_call.get("name") == "get_service_info":
                bot_response = "Con gusto, te cuento sobre los servicios de Crezgo: estrategia empresarial, finanzas, marketing digital y outsourcing financiero. ¿Hay algún área específica que quieras fortalecer?"
            elif tool_call.get("name") == "schedule_meeting":
                bot_response = "Perfecto, puedo ayudarte a agendar una llamada de diagnóstico. ¿Qué día y hora te convienen para que uno de nuestros asesores te contacte?"
            else:
                bot_response = "Parece que necesitas ayuda con algo que requiere una herramienta, pero no estoy seguro de cuál. ¿Puedes reformular tu pregunta?"

        else:  # decision == 'clarify' or other
            bot_response = "No estoy seguro de cómo ayudarte con eso. ¿Podrías darme más detalles o hacer otra pregunta?"

        # 3. Log the conversation
        self.supabase_adapter.log_conversation(
            user_id=user_id,
            user_query=user_query,
            bot_response=bot_response,
            context_chunks=[
                str(c) for c in context_chunks
            ],  # Ensure context is stringified
        )

        return bot_response
