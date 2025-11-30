from typing import Optional

class WakeWordDetector:
    """
    Skeleton wake-word detector for 'hey baymax'.
    Real implementation will use audio classification or signal processing.
    """

    def __init__(self, wakeword: str = "hey baymax"):
        self.wakeword = wakeword.lower()

    def detect(self, audio_chunk: Optional[bytes]) -> bool:
        """
        Placeholder wake-word detection.
        Always returns False for now.

        TODO:
        - Add VAD (Voice Activity Detection)
        - Add MFCC or audio feature extraction
        - Add wake-word classification model
        - Add fuzzy matching
        """
        # Defensive programming: handle None or empty input
        if audio_chunk is None or len(audio_chunk) == 0:
            print("[WakeWord] detect() received empty audio (skeleton).")
            return False

        print("[WakeWord] detect() called (skeleton).")
        return False  # Always false until the real model is
