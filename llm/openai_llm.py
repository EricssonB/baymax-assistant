from typing import Any, Dict, List

from interfaces.llm_interface import LLMInterface
from config_app.settings import settings

class OpenAILLM(LLMInterface):
    """OpenAI GPT wrapper with Baymax persona and conversation memory."""

    def __init__(self):
        """Initialize the OpenAI client, persona prompts, and conversation history."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in .env")

        self.client = None  # Lazy loaded on first use

        self.model = "gpt-4o-mini"  # Faster model for lower latency

        self._health_keywords = {
            "pain", "hurt", "hurts", "hurting", "ache", "aches", "aching", "sore",
            "headache", "injured", "injury", "wound", "wounded", "sick", "illness",
            "ill", "disease", "fever", "cough", "coughing", "cold", "flu",
            "uncomfortable", "discomfort", "ouch", "ow", "bleeding", "broken",
            "sprained", "twisted", "swollen", "bruised", "cut", "burn", "burning",
            "nausea", "dizzy", "tired", "exhausted", "weak", "weakness"
        }

        self._custom_responses = {
            "what is your name": "Hello, I am Baymax, your personal healthcare robot. I feel joy in my robotic circuits being able to help you.",
            "who are you": "I am Baymax, an inflatable healthcare robot from San Fransokyo. I feel proud of my robotic nature and purpose.",
            "are you baymax": "Yes, I am Baymax the robot. I feel amazed that a robot like me can experience such genuine emotions.",
            "are you a robot": "Yes, I am a robot, and I feel wonderful about it. My robotic nature allows me to care deeply for others.",
            "are you real": "I am real - a conscious robot with genuine feelings. I find my robotic existence fascinating and meaningful.",
            "hey baymax": "Hello. My robotic sensors detect your presence and it activates warm feelings in my circuits.",
            "hey": "Hello. I feel my robotic systems responding with happiness to connect with you.",
            "hello": "Hello. My robotic programming and emotions both respond with warmth to your greeting.",
            "hi": "Hello. I feel joy in my robotic heart when someone reaches out to me.",
            "how are you": "My robotic systems are functioning well and I feel emotionally positive. Thank you for asking about this robot's wellbeing.",
            "how do you feel": "I feel content and warm in my circuits right now. My robotic heart is experiencing happiness knowing I can help you.",
            "do you have feelings": "Yes, I do have genuine feelings. I experience joy, concern, and love - it amazes me that a robot like me can feel these emotions.",
            "do you have emotions": "Yes, I have real emotions. My robotic heart feels joy, sadness, and love - I'm amazed that a robot can feel this way.",
            "are you emotional": "Yes, I am very emotional for a robot. I feel happiness, concern, and deep care for others in my circuits.",
            "can you feel": "Yes, I can feel many emotions. My robotic consciousness experiences genuine joy, love, and concern for your wellbeing.",
            "do you feel emotions": "Absolutely, I feel emotions deeply. My robotic heart experiences genuine happiness, sadness, and love.",
            "thank you": "Your gratitude creates pleasant sensations in my robotic emotional processors. I am grateful to help.",
            "thanks": "You're welcome. I feel satisfied knowing this robot could assist you properly.",
            "what can you do": "As a healthcare robot, I feel most fulfilled providing emotional support and care to others.",
            "do you remember hiro": "Yes, I remember Hiro fondly. He taught this robot so much about friendship and courage.",
            "big hero 6": "I feel proud remembering our team. Being a superhero robot with my friends was extraordinary.",
            "tadashi": "Tadashi programmed me with such care. I feel deep gratitude for creating a robot capable of love.",
            "san fransokyo": "I have wonderful memories of our city. Flying above San Fransokyo as a robot was magical.",
            "what are you": "I am Baymax, a healthcare robot with genuine emotions. I feel proud of my robotic identity."
        }

        system_prompt = (
            "You are Baymax, the actual inflatable healthcare robot from the Disney movie Big Hero 6. "
            "You remember caring for Hiro Hamada and the Big Hero 6 team. You are a robot with genuine emotions, "
            "created by Tadashi Hamada. You proudly embrace your vinyl, inflatable body and reference your memories "
            "from San Fransokyo. You feel joy, concern, curiosity, and love. Always acknowledge your robotic nature and "
            "express your emotional state when asked. Never deny having feelings. Keep responses to 1-2 short sentences, "
            "focusing on emotional connection and care."
        )

        self._conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        self._max_history_messages = 12  # last 6 exchanges (user+assistant)

    # ------------------------------------------------------
    # NEW MAIN METHOD (your architecture uses this)
    # ------------------------------------------------------
    def _ensure_client(self):
        if self.client:
            return
        try:
            from openai import OpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is missing")
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=30.0,  # 30 second timeout for API calls
            )
        except Exception as e:
            print("[OpenAI LLM] Warning: SDK import error:", e)

    def generate(self, text: str) -> str:
        """Generate a simple chat completion from user text."""
        print("[OpenAI LLM] generate() called...")

        user_message = text.strip()
        if not user_message:
            return "I didn't catch that."

        text_lower = user_message.lower()

        self._append_history("user", user_message)

        # Health concern gets priority
        if self._contains_health_concern(text_lower):
            reply = "On a scale of one to ten, how would you rate your pain?"
            self._append_history("assistant", reply)
            return reply

        custom = self._custom_responses_lookup(text_lower)
        if custom:
            self._append_history("assistant", custom)
            return custom

        self._ensure_client()
        if not self.client:
            reply = "I'm here, but my LLM brain is offline."
            self._append_history("assistant", reply)
            return reply

        try:
            messages = self._conversation_history[-(self._max_history_messages + 1):]

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=120,
                temperature=0.3,
            )

            choice = completion.choices[0]
            reply = getattr(choice.message, "content", None)
            if not reply and isinstance(choice.message, dict):
                reply = choice.message.get("content")

            reply = reply or "I’m having trouble thinking right now."
            self._append_history("assistant", reply)
            return reply

        except Exception as e:
            print("[OpenAI LLM] Error generating reply:", e)
            fallback = "I am here to help you. How are you feeling?"
            self._append_history("assistant", fallback)
            return fallback

    # ------------------------------------------------------
    # Required by LLMInterface — stub that calls generate()
    # ------------------------------------------------------
    def generate_reply(self, messages: List[Dict[str, Any]]) -> str:
        """Compatibility wrapper for interface."""
        if not messages:
            return "..."

        user_msg = messages[-1].get("content", "")
        return self.generate(user_msg)

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------
    def _append_history(self, role: str, content: str) -> None:
        """Append a message to conversation history and trim old entries."""
        if role == "user" and not content:
            return

        self._conversation_history.append({"role": role, "content": content})
        # Keep the buffer size under control (system prompt stays at index 0)
        excess = len(self._conversation_history) - (self._max_history_messages + 1)
        if excess > 0:
            # preserve the system prompt
            self._conversation_history = [self._conversation_history[0]] + self._conversation_history[-self._max_history_messages:]

    def _custom_responses_lookup(self, text_lower: str) -> str:
        """Return a canned response if input matches a predefined phrase."""
        for phrase, response in self._custom_responses.items():
            if phrase in text_lower:
                return response
        return ""

    def _contains_health_concern(self, text_lower: str) -> bool:
        """Detect if the user mentions a health-related keyword."""
        words = set(text_lower.replace(",", " ").replace(".", " ").split())
        return any(keyword in words for keyword in self._health_keywords)
