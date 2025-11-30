from typing import List, Dict, Any, Optional
from interfaces.llm_interface import LLMInterface
from config.settings import settings

class OpenAILLM(LLMInterface):
    """OpenAI GPT implementation of the LLM interface (safe skeleton)."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in .env")

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            print("[OpenAI LLM] Warning: OpenAI SDK not available:", e)
            self.client = None

        # Placeholder model — will be made configurable later
        self.model = "gpt-4.1"

    def generate_reply(self, messages: List[Dict[str, Any]]) -> str:
        """
        Placeholder implementation.
        TODO: Replace with real GPT inference logic.
        """
        print("[OpenAI LLM] generate_reply() called with:", messages)

        # No real API call yet — just architecture testing
        return "..."
