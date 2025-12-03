from interfaces.state_interface import State


class ProcessingState(State):
    def __init__(self, llm=None):
        self.llm = llm

    def on_enter(self):
        print("[State] >>> ProcessingState")

    def on_exit(self):
        print("[State] <<< ProcessingState")

    def handle(self, manager, user_input):
        text = manager.last_user_text or user_input
        print(f"[ProcessingState] Handling: {text}")

        if not text:
            print("[ProcessingState] No user text to process.")
            manager.last_bot_text = "I didn't catch that."
            manager.set_post_speech_state(manager.listening_state)
            return manager.speaking_state

        # --- LLM CALL HERE ---
        reply = "Okay."

        llm_engine = self.llm or getattr(manager, "llm", None)
        if llm_engine:
            try:
                print("[ProcessingState] Generating LLM response...")
                reply = llm_engine.generate(text)
            except Exception as e:
                print("[ProcessingState] LLM error:", e)

        # ⭐ Store the reply for SpeakingState
        manager.last_bot_text = reply
        manager.set_post_speech_state(manager.listening_state)

        # Clear the user text so it doesn't repeat
        manager.last_user_text = None

        return manager.speaking_state
