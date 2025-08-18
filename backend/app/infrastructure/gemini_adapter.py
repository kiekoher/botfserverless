import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiAdapter:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY must be set in environment.")
        genai.configure(api_key=api_key)

        # TODO: Make model names configurable
        self.embedding_model = "models/embedding-001"
        self.generative_model = genai.GenerativeModel("gemini-1.5-flash")

    async def get_embedding(self, text: str):
        """
        Generates embeddings for a given text.
        """
        try:
            result = genai.embed_content(model=self.embedding_model, content=text)
            return result["embedding"]
        except Exception as e:
            print(f"Error generating embedding with Gemini: {e}")
            return None

    async def classify_and_extract(self, query: str) -> dict:
        """
        Classifies the user's intent and extracts information using a Gemini function call.
        This is a simplified version of the logic from the original bot.
        In a real scenario, this would be more robust.
        """
        # This is a placeholder for the classification logic.
        # A real implementation would use a more sophisticated prompt and function calling.
        if "servicio" in query.lower():
            return {"decision": "use_tool", "tool_call": {"name": "get_service_info"}}
        if "agendar" in query.lower() or "reunión" in query.lower():
            return {"decision": "use_tool", "tool_call": {"name": "schedule_meeting"}}

        return {"decision": "use_rag", "summary_for_rag": query}

    async def generate_rag_response(
        self, query: str, context: list, history: list
    ) -> str:
        """
        Generates a response using the RAG pattern, incorporating context and history.
        """
        # Build the prompt
        prompt = f"""
        Eres EVA, una asesora experta de Crezgo. Tu objetivo es ayudar a dueños de pymes a resolver sus dudas de negocio.
        Basándote EXCLUSIVAMENTE en el siguiente contexto y en el historial de la conversación, responde la pregunta del usuario.
        Si el contexto no es suficiente para responder, di que no tienes la información y pregunta si puedes ayudar en algo más.

        Contexto proporcionado:
        ---
        {context}
        ---

        Historial de la conversación:
        ---
        {history}
        ---

        Pregunta del usuario: {query}

        Respuesta:
        """
        try:
            response = self.generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating RAG response with Gemini: {e}")
            return "Lo siento, no pude procesar tu solicitud en este momento."
