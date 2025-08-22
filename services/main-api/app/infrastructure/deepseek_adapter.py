import os
from openai import AsyncOpenAI

class DeepSeekV2Adapter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set.")
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )

    async def generate_response(self, prompt: str, history: list) -> str:
        print("--- DeepSeek V2 (Analysis) ---")
        print(f"Prompt: {prompt}")
        try:
            messages = [{"role": "system", "content": prompt}]
            # A real implementation would format the history correctly
            # For now, we are focusing on the prompt

            response = await self.client.chat.completions.create(
                model="deepseek-coder", # As specified in AGENT.md for analysis
                messages=messages,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ An error occurred while calling the DeepSeek API: {e}")
            return "Error: Could not get response from DeepSeek V2."

class DeepSeekChatAdapter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set.")
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )

    async def generate_response(self, prompt: str, history: list) -> str:
        print("--- DeepSeek Chat (Extraction) ---")
        print(f"Prompt: {prompt}")
        try:
            messages = [{"role": "system", "content": prompt}]
            # A real implementation would format the history correctly

            response = await self.client.chat.completions.create(
                model="deepseek-chat", # As specified in AGENT.md for extraction
                messages=messages,
                max_tokens=1024,
                temperature=0, # Lower temperature for more deterministic output (good for JSON)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ An error occurred while calling the DeepSeek API: {e}")
            return "Error: Could not get response from DeepSeek Chat."
