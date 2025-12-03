import os
import subprocess
import time

from interfaces.state_interface import State
from config_app.settings import settings

class SpeakingState(State):
    """
    SpeakingState:
    - Uses ElevenLabsTTS.speak() to generate audio
    - Audio saved automatically by the TTS class
    - Plays the output using macOS `afplay`
    """

    def __init__(self, tts=None):
        self.tts = tts

    def on_enter(self):
        print("[State] >>> SpeakingState")

    def on_exit(self):
        print("[State] <<< SpeakingState")

    def handle(self, manager, user_input):
        print("[SpeakingState] Handling:", user_input)

        # Get the bot reply
        if not hasattr(manager, "last_bot_text") or not manager.last_bot_text:
            print("[SpeakingState] No bot response available.")
            return manager.idle_state

        response_text = manager.last_bot_text
        print(f"[SpeakingState] Speaking: {response_text}")

        manager.notify_speaking_start()

        audio_duration = 0.0
        try:
            # Generate speech audio
            tts_engine = self.tts or getattr(manager, "tts", None)
            if tts_engine:
                try:
                    tts_engine.speak(response_text)
                    audio_duration = getattr(tts_engine, "last_duration", 0.0)

                    output_path = getattr(tts_engine, "output_path", "audio/output.wav")
                    skip_playback = os.getenv("BAYMAX_SKIP_AUDIO") == "1"
                    if skip_playback:
                        pass
                    elif not os.path.exists(output_path):
                        print(f"[SpeakingState] Expected audio file not found at {output_path}")
                    else:
                        # Use subprocess for better error reporting than os.system
                        subprocess.run(["afplay", output_path], check=True)
                        settle_time = max(settings.TTS_POST_BUFFER / 2.0, 0.0)
                        if settle_time:
                            time.sleep(settle_time)

                except Exception as e:
                    print("[SpeakingState] TTS error:", e)
            else:
                print("[SpeakingState] No TTS engine available.")
        finally:
            manager.notify_speaking_end(audio_duration)

        # Prevent the same line from replaying if we loop back here without new text
        manager.last_bot_text = None

        next_state = manager.consume_post_speech_state() or manager.idle_state
        return next_state
