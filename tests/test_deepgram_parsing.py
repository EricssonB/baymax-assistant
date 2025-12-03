import unittest
from typing import Any, Dict, cast

from stt.deepgram_stt import _extract_transcript
from stt.deepgram_live import _to_dict_safe


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
        from deepgram.clients.prerecorded.v1.response import PrerecordedResponse

        from_dict = cast(Any, PrerecordedResponse).from_dict

        response_obj = from_dict(
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
        from deepgram.clients.live.v1.response import LiveResultResponse

        from_dict = cast(Any, LiveResultResponse).from_dict

        result_obj = from_dict(
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
