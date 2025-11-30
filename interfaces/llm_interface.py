from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMInterface(ABC):
    """Interface for LLM-based response generation."""

    @abstractmethod
    def generate_reply(self, messages: List[Dict[str, Any]]) -> str:
        """
        Generate a response given a list of chat messages.
        messages follows the OpenAI-style format:
        [{"role": "user" | "assistant" | "system", "content": "..."}]
        """
        pass
