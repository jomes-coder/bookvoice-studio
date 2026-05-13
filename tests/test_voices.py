import unittest
from pathlib import Path
from unittest.mock import patch

from bookvoice.voices import (
    COMMON_VOICES,
    extract_voice_short_names,
    format_voice_label,
    format_voice_labels,
    verify_voice_can_speak,
    voice_id_from_label,
)


class VoiceHelperTests(unittest.TestCase):
    def test_common_voices_include_expected_chinese_voices(self):
        self.assertIn("zh-CN-YunxiaNeural", COMMON_VOICES)
        self.assertIn("zh-CN-YunxiNeural", COMMON_VOICES)
        self.assertIn("zh-CN-YunjianNeural", COMMON_VOICES)
        self.assertIn("zh-CN-XiaoxiaoNeural", COMMON_VOICES)

    def test_extract_voice_short_names_sorts_and_deduplicates(self):
        voices = [
            {"ShortName": "zh-CN-YunxiNeural"},
            {"ShortName": "en-US-AriaNeural"},
            {"ShortName": "zh-CN-YunxiNeural"},
            {"Locale": "zh-CN"},
        ]

        names = extract_voice_short_names(voices)

        self.assertEqual(names, ["en-US-AriaNeural", "zh-CN-YunxiNeural"])

    def test_format_voice_label_uses_chinese_description_for_known_voice(self):
        label = format_voice_label("zh-CN-XiaoxiaoNeural")

        self.assertEqual(label, "晓晓 - 女声，普通话（zh-CN-XiaoxiaoNeural）")

    def test_voice_id_from_label_extracts_short_name(self):
        voice_id = voice_id_from_label("晓晓 - 女声，普通话（zh-CN-XiaoxiaoNeural）")

        self.assertEqual(voice_id, "zh-CN-XiaoxiaoNeural")

    def test_format_voice_labels_preserves_unknown_voice_id(self):
        labels = format_voice_labels(["en-US-AriaNeural", "zh-CN-XiaoxiaoNeural"])

        self.assertEqual(
            labels,
            [
                "en-US-AriaNeural",
                "晓晓 - 女声，普通话（zh-CN-XiaoxiaoNeural）",
            ],
        )

    def test_verify_voice_can_speak_writes_and_removes_probe_file(self):
        saved_paths = []
        calls = []

        class FakeCommunicate:
            def __init__(self, text, voice, **kwargs):
                calls.append((text, voice, kwargs))

            async def save(self, output_path):
                saved_paths.append(Path(output_path))
                Path(output_path).write_bytes(b"mp3")

        with patch("bookvoice.voices.edge_tts.Communicate", FakeCommunicate):
            import asyncio

            asyncio.run(
                verify_voice_can_speak(
                    "zh-CN-XiaoxiaoNeural",
                    rate="+15%",
                    volume="+5%",
                    pitch="+2Hz",
                )
            )

        self.assertEqual(len(saved_paths), 1)
        self.assertFalse(saved_paths[0].exists())
        self.assertEqual(
            calls,
            [
                (
                    "你好，这是音色测试。",
                    "zh-CN-XiaoxiaoNeural",
                    {"rate": "+15%", "volume": "+5%", "pitch": "+2Hz"},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()

