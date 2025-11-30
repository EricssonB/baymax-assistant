# -----------------------------
# Baymax 2.0 – System Wiring (Architecture Skeleton)
# -----------------------------

# Import StateManager and subsystems
from states.state_manager import StateManager
from audio.microphone import Microphone
from stt.deepgram_stt import DeepgramSTT
from llm.openai_llm import OpenAILLM
from tts.elevenlabs_tts import ElevenLabsTTS
from wakeword.wakeword_detector import WakeWordDetector

print("Starting Baymax 2.0 (Subsystem Wiring Skeleton)...")

# -----------------------------
# Instantiate Subsystems (placeholders for now)
# -----------------------------
audio = Microphone()
stt = DeepgramSTT()
llm = OpenAILLM()
tts = ElevenLabsTTS()
wakeword = WakeWordDetector()

# -----------------------------
# Create State Manager
# -----------------------------
# IMPORTANT:
# StateManager internally creates all state objects and begins in SleepState.
manager = StateManager()

# -----------------------------
# Demo Loop (Architecture Only)
# -----------------------------
# Added extra step so SpeakingState actually runs.
demo_inputs = [
    None,            # SleepState
    "hey baymax",    # Wake word → WakeState
    "user speech",   # WakeState → ListeningState
    "response",      # ListeningState → ProcessingState
    None,            # ProcessingState returns SpeakingState
    "final step"     # SpeakingState now has a turn to execute!
]

for demo in demo_inputs:
    print("\n[Demo] Input:", demo)
    manager.update(user_input=demo)
