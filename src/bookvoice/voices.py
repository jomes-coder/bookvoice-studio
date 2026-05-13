from collections.abc import Iterable
import os
import tempfile
from typing import Any

import edge_tts


VOICE_DISPLAY_NAMES = {
    "zh-CN-XiaoxiaoNeural": "晓晓 - 女声，普通话",
    "zh-CN-XiaoyiNeural": "晓伊 - 女声，普通话",
    "zh-CN-YunjianNeural": "云健 - 男声，普通话",
    "zh-CN-YunxiNeural": "云希 - 男声，普通话",
    "zh-CN-YunxiaNeural": "云夏 - 女声，少儿/自然",
    "zh-CN-YunyangNeural": "云扬 - 男声，新闻播报",
}

COMMON_VOICES = [
    "zh-CN-YunxiaNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-YunjianNeural",
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunyangNeural",
]


def extract_voice_short_names(voices: Iterable[dict[str, Any]]) -> list[str]:
    names = {
        voice["ShortName"]
        for voice in voices
        if isinstance(voice, dict) and isinstance(voice.get("ShortName"), str)
    }
    return sorted(names)


def format_voice_label(short_name: str) -> str:
    display_name = VOICE_DISPLAY_NAMES.get(short_name)
    if not display_name:
        return short_name
    return f"{display_name}（{short_name}）"


def format_voice_labels(short_names: Iterable[str]) -> list[str]:
    return [format_voice_label(short_name) for short_name in short_names]


def voice_id_from_label(label: str) -> str:
    stripped = label.strip()
    if "（" in stripped and stripped.endswith("）"):
        return stripped.rsplit("（", 1)[1][:-1]
    if "(" in stripped and stripped.endswith(")"):
        return stripped.rsplit("(", 1)[1][:-1]
    return stripped


async def verify_voice_can_speak(
    voice: str,
    probe_text: str = "你好，这是音色测试。",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    temp_output = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            temp_output = tmp_file.name

        await edge_tts.Communicate(
            probe_text,
            voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
        ).save(temp_output)
        if not os.path.exists(temp_output) or os.path.getsize(temp_output) <= 0:
            raise ValueError(f"No audio was generated for voice: {voice}")
    finally:
        if temp_output and os.path.exists(temp_output):
            os.remove(temp_output)


async def fetch_edge_tts_voice_names() -> list[str]:
    voices = await edge_tts.list_voices()
    names = extract_voice_short_names(voices)
    return names or COMMON_VOICES.copy()
