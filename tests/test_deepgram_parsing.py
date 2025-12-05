import unittest
import json
from typing import Any, Dict, cast

from stt.deepgram_stt import _extract_transcript
from stt.deepgram_live import _to_dict_safe


class MockSdkObject:
    """Simulates a Deepgram SDK object with to_dict/to_json methods."""
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def to_dict(self) -> Dict[str, Any]:
        return self._data

    def to_json(self) -> str:
        return json.dumps(self._data)


class TestDeepgramParsing(unittest.TestCase):
    def test_extract_transcript_from_dict(self) -> None:
        response = {
            "results": {
                "channels": [
                    {
                        "alternatives": [
                            {
                                "transcript": "hello world",
                            }
                        ]
                    }
                ]
            }
        }

        self.assertEqual(_extract_transcript(response), "hello world")

    def test_extract_transcript_from_sdk_object(self) -> None:
        # Simulate the SDK object structure
        response_obj = MockSdkObject(
            {
                "metadata": {},
                "results": {
                    "channels": [
                        {
                            "alternatives": [
                                {
                                    "transcript": "baymax online",
                                }
                            ]
                        }
                    ]
                },
            }
        )

        self.assertEqual(_extract_transcript(response_obj), "baymax online")

    def test_to_dict_safe_live_response(self) -> None:
        # Simulate the LiveResultResponse object
        result_obj = MockSdkObject(
            {
                "channel": {
                    "alternatives": [
                        {
                            "transcript": "wake up",
                            "confidence": 0.9,
                        }
                    ]
                },
                "is_final": True,
            }
        )

        converted = _to_dict_safe(result_obj)
        self.assertIsInstance(converted, dict)
        converted_dict = cast(Dict[str, Any], converted)
        self.assertTrue(converted_dict.get("is_final"))
        self.assertEqual(
            converted_dict["channel"]["alternatives"][0]["transcript"],
            "wake up",
        )


if __name__ == "__main__":
    unittest.main()
