# -----------------------------
# Baymax 2.0 – System Wiring (Architecture Skeleton)
# -----------------------------

# Import states
from states.sleep_state import SleepState
from states.wake_state import WakeState
from states.listening_state import ListeningState
from states.processing_state import ProcessingState
from states.speaking_state import SpeakingState
from states.idle_state import IdleState
from states.state_manager import StateManager

# Subsystems (not wired yet – architecture only)
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
# Instantiate States
# -----------------------------
sleep_state = SleepState()
wake_state = WakeState()
listening_state = ListeningState()
processing_state = ProcessingState()
speaking_state = SpeakingState()
idle_state = IdleState()

# Optional demo-only circular chain (not required, but helps visualize flow)
sleep_state.next = wake_state
wake_state.next = listening_state
listening_state.next = processing_state
processing_state.next = speaking_state
speaking_state.next = idle_state
idle_state.next = sleep_state

# -----------------------------
# Create State Manager
# -----------------------------
# IMPORTANT:
# StateManager() takes NO arguments in this version.
# It internally creates its own state registry and starts in SleepState.
manager = StateManager()

# -----------------------------
# Demo Loop (Architecture Only)
# -----------------------------
demo_inputs = ["None", "hey baymax", "user speech", "response", "None"]

for demo in demo_inputs:
    print("\n[Demo] Input:", demo)
    manager.update(user_input=demo)
