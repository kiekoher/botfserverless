import os

class DeepSeekV2Adapter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    async def generate_response(self, prompt: str, history: list) -> str:
        print(f"--- DeepSeek V2 (Analysis) ---")
        print(f"Prompt: {prompt}")
        print(f"History: {history}")
        # In a real implementation, you would call the DeepSeek API
        return f"DeepSeek V2 analysis of '{prompt}' (simulated)"

class DeepSeekChatAdapter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    async def generate_response(self, prompt: str, history: list) -> str:
        print(f"--- DeepSeek Chat (Extraction) ---")
        print(f"Prompt: {prompt}")
        print(f"History: {history}")
        # In a real implementation, you would call the DeepSeek API
        return f"DeepSeek Chat extracted data from '{prompt}' (simulated)"
