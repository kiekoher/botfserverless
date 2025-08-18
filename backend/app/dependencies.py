from app.infrastructure.supabase_adapter import SupabaseAdapter
from app.infrastructure.gemini_adapter import GeminiAdapter
from app.core.use_cases.process_chat_message import ProcessChatMessage

# Create singleton instances of our adapters
supabase_adapter = SupabaseAdapter()
gemini_adapter = GeminiAdapter()


def get_process_chat_message_use_case() -> ProcessChatMessage:
    """
    Dependency injector for the ProcessChatMessage use case.
    """
    return ProcessChatMessage(supabase_adapter, gemini_adapter)
