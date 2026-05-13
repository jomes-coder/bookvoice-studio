# Desktop GUI and Voice Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a source-run Tkinter desktop GUI with expanded voice selection, conversion speed controls, and shared validation for the existing epub2mp3 converter.

**Architecture:** Keep the existing `EpubToMP3Converter` as the conversion engine, but make its logging, concurrency, and post-processing options injectable. Add small helper modules for validation and voice list handling so CLI and GUI use the same behavior. Add `src/epub2mp3/gui.py` as the Tkinter entry point.

**Tech Stack:** Python 3.12, Tkinter, asyncio, unittest, edge-tts, ebooklib, mutagen, imageio-ffmpeg.

---

## Repository Note

`D:\product\epub2mp3` is not currently a git repository, so task-level commit steps are replaced by checkpoint notes. If the project is initialized as a git repository before implementation, commit after each task using the files listed in that task.

## File Structure

- Create: `src/epub2mp3/options.py`
  - Owns the shared conversion option dataclass and input validation.
- Create: `src/epub2mp3/voices.py`
  - Owns built-in voice names, voice name extraction, and Edge TTS voice refresh.
- Modify: `src/epub2mp3/main.py`
  - Keeps the CLI entry point and converter class.
  - Adds bounded concurrency, injectable logging, post-processing toggles, parser construction, and shared validation use.
- Modify: `src/epub2mp3/utils.py`
  - Allows existing audio helper functions to log through an injected logger while defaulting to `print`.
- Create: `src/epub2mp3/gui.py`
  - Owns the Tkinter window, background workers, file pickers, validation display, voice refresh, and conversion launch.
- Modify: `pyproject.toml`
  - Adds `pdm gui`.
- Modify: `README.md`
  - Documents the GUI command, new CLI speed flags, and fixes the background music voice example.
- Create: `tests/test_options.py`
  - Tests shared validation.
- Create: `tests/test_voices.py`
  - Tests built-in voices and voice short-name extraction.
- Create: `tests/test_converter_options.py`
  - Tests concurrency limiting and optional post-processing behavior.
- Create: `tests/test_cli_parser.py`
  - Tests new CLI flags without running conversion.
- Create: `tests/test_gui_import.py`
  - Verifies the GUI module is importable and exposes a launch function without creating a window at import time.

---

### Task 1: Shared Conversion Options and Validation

**Files:**
- Create: `src/epub2mp3/options.py`
- Test: `tests/test_options.py`

- [ ] **Step 1: Write the failing validation tests**

Create `tests/test_options.py`:

```python
import tempfile
import unittest
from pathlib import Path

from epub2mp3.options import ConversionOptions, validate_conversion_inputs


class ConversionOptionsTests(unittest.TestCase):
    def test_valid_inputs_have_no_errors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            output_dir = root / "out"
            bg_dir = root / "bg"
            bg_dir.mkdir()

            options = ConversionOptions(
                epub_path=str(epub_path),
                output_dir=str(output_dir),
                voice="zh-CN-YunxiaNeural",
                retries=3,
                bg_dir=str(bg_dir),
                max_concurrency=3,
                enable_high_quality=True,
                enable_lyrics=True,
            )

            self.assertEqual(validate_conversion_inputs(options), [])

    def test_rejects_missing_epub_path(self):
        options = ConversionOptions(epub_path="", output_dir="output_audio")

        errors = validate_conversion_inputs(options)

        self.assertIn("EPUB file path is required.", errors)

    def test_rejects_nonexistent_epub_path(self):
        options = ConversionOptions(
            epub_path="missing.epub",
            output_dir="output_audio",
        )

        errors = validate_conversion_inputs(options)

        self.assertIn("EPUB file does not exist: missing.epub", errors)

    def test_rejects_epub_path_that_is_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options = ConversionOptions(
                epub_path=temp_dir,
                output_dir="output_audio",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn(f"EPUB path is not a file: {temp_dir}", errors)

    def test_rejects_empty_output_dir(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Output directory is required.", errors)

    def test_rejects_invalid_retry_count(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                retries=0,
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Retry count must be at least 1.", errors)

    def test_rejects_invalid_concurrency(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                max_concurrency=0,
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Concurrent chapter count must be at least 1.", errors)

    def test_rejects_invalid_background_music_directory(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                bg_dir="missing-bg",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Background music directory does not exist: missing-bg", errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```shell
pdm run python -m unittest tests.test_options -v
```

Expected: FAIL or ERROR with `ModuleNotFoundError: No module named 'epub2mp3.options'`.

- [ ] **Step 3: Add the shared options module**

Create `src/epub2mp3/options.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_VOICE = "zh-CN-YunxiaNeural"
DEFAULT_OUTPUT_DIR = "output_audio"
DEFAULT_RETRIES = 3
DEFAULT_MAX_CONCURRENCY = 3


@dataclass(frozen=True)
class ConversionOptions:
    epub_path: str
    output_dir: str
    voice: str = DEFAULT_VOICE
    retries: int = DEFAULT_RETRIES
    bg_dir: Optional[str] = None
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    enable_high_quality: bool = True
    enable_lyrics: bool = True


def validate_conversion_inputs(options: ConversionOptions) -> list[str]:
    errors: list[str] = []

    if not options.epub_path:
        errors.append("EPUB file path is required.")
    else:
        epub_path = Path(options.epub_path)
        if not epub_path.exists():
            errors.append(f"EPUB file does not exist: {options.epub_path}")
        elif not epub_path.is_file():
            errors.append(f"EPUB path is not a file: {options.epub_path}")

    if not options.output_dir:
        errors.append("Output directory is required.")

    if options.retries < 1:
        errors.append("Retry count must be at least 1.")

    if options.max_concurrency < 1:
        errors.append("Concurrent chapter count must be at least 1.")

    if options.bg_dir:
        bg_path = Path(options.bg_dir)
        if not bg_path.exists():
            errors.append(f"Background music directory does not exist: {options.bg_dir}")
        elif not bg_path.is_dir():
            errors.append(f"Background music path is not a directory: {options.bg_dir}")

    return errors
```

- [ ] **Step 4: Run the validation tests**

Run:

```shell
pdm run python -m unittest tests.test_options -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Record changed files:

```text
src/epub2mp3/options.py
tests/test_options.py
```

---

### Task 2: Built-In and Refreshable Voice Helpers

**Files:**
- Create: `src/epub2mp3/voices.py`
- Test: `tests/test_voices.py`

- [ ] **Step 1: Write the failing voice helper tests**

Create `tests/test_voices.py`:

```python
import unittest

from epub2mp3.voices import COMMON_VOICES, extract_voice_short_names


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```shell
pdm run python -m unittest tests.test_voices -v
```

Expected: FAIL or ERROR with `ModuleNotFoundError: No module named 'epub2mp3.voices'`.

- [ ] **Step 3: Add the voice helper module**

Create `src/epub2mp3/voices.py`:

```python
from collections.abc import Iterable
from typing import Any

import edge_tts


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


async def fetch_edge_tts_voice_names() -> list[str]:
    voices = await edge_tts.list_voices()
    names = extract_voice_short_names(voices)
    return names or COMMON_VOICES.copy()
```

- [ ] **Step 4: Run the voice tests**

Run:

```shell
pdm run python -m unittest tests.test_voices -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Record changed files:

```text
src/epub2mp3/voices.py
tests/test_voices.py
```

---

### Task 3: Converter Concurrency, Logging, and Post-Processing Options

**Files:**
- Modify: `src/epub2mp3/main.py`
- Modify: `src/epub2mp3/utils.py`
- Test: `tests/test_converter_options.py`

- [ ] **Step 1: Write failing converter behavior tests**

Create `tests/test_converter_options.py`:

```python
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from epub2mp3.main import EpubToMP3Converter


class InstrumentedConverter(EpubToMP3Converter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = 0
        self.max_seen = 0

    async def process_chapter(self, index, title, content, output_path, failed_chapters):
        self.active += 1
        self.max_seen = max(self.max_seen, self.active)
        await asyncio.sleep(0.01)
        self.active -= 1


class ConverterOptionsTests(unittest.TestCase):
    def test_convert_epub_respects_max_concurrency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")

            converter = InstrumentedConverter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                max_concurrency=2,
                logger=lambda message: None,
            )
            chapters = [(f"Chapter {i}", "content") for i in range(6)]

            with patch("epub2mp3.main.get_chapters", return_value=chapters):
                asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertLessEqual(converter.max_seen, 2)

    def test_process_chapter_skips_disabled_post_processing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "chapter.mp3"

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                enable_high_quality=False,
                enable_lyrics=False,
                logger=lambda message: None,
            )

            async def fake_tts(text, output_file):
                Path(output_file).write_bytes(b"mp3")

            converter.text_to_speech_with_retry = fake_tts

            with patch("epub2mp3.main.convert_mp3_high_quality") as transcode:
                with patch("epub2mp3.main.write_lyrics_to_mp3") as lyrics:
                    asyncio.run(
                        converter.process_chapter(
                            1,
                            "Chapter",
                            "content",
                            str(output_path),
                            [],
                        )
                    )

            transcode.assert_not_called()
            lyrics.assert_not_called()
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the converter tests to verify they fail**

Run:

```shell
pdm run python -m unittest tests.test_converter_options -v
```

Expected: FAIL with `TypeError` for unsupported `max_concurrency`, `enable_high_quality`, `enable_lyrics`, or `logger`.

- [ ] **Step 3: Update utility functions to accept injected logging**

In `src/epub2mp3/utils.py`, add `Callable` to imports:

```python
from typing import Tuple, List, Callable
```

Change `write_lyrics_to_mp3` signature and replace its `print` calls:

```python
def write_lyrics_to_mp3(
    mp3_path: str,
    lyrics_text: str,
    logger: Callable[[str], None] = print,
):
    """将文本作为带均匀时间标签的歌词写入mp3的歌词标签"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        duration = int(audio.info.length)
        if duration < 1:
            logger(f"[{mp3_path}] 写入歌词标签失败: 音频时长过短 (小于1秒)。")
            return
        lrc_text = make_lrc_lines_by_duration(lyrics_text, duration)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.delall("USLT")
        audio.tags.add(
            USLT(encoding=Encoding.UTF8, lang="chi", desc="epub2mp3", text=lrc_text)
        )
        audio.save()
        logger(f"[{mp3_path}] 歌词标签写入成功")
    except Exception as e:
        logger(f"[{mp3_path}] 写入歌词标签失败: {e}")
```

Change `convert_mp3_high_quality` signature and replace its `print` calls:

```python
def convert_mp3_high_quality(
    input_mp3,
    bitrate="320k",
    samplerate="48000",
    logger: Callable[[str], None] = print,
):
    """
    用ffmpeg把mp3转为最高比特率和采样率（如320kbps/48kHz）
    直接修改原始文件
    """
    try:
        ffmpeg_path = get_ffmpeg_exe()

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            temp_output = tmp_file.name

        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_mp3,
            "-ar",
            samplerate,
            "-b:a",
            bitrate,
            "-map_metadata",
            "0",
            temp_output,
        ]

        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        os.replace(temp_output, input_mp3)

        logger(f"[{input_mp3}] 已提升到 {bitrate}, {samplerate}Hz")

    except Exception as e:
        if "temp_output" in locals():
            try:
                os.remove(temp_output)
            except OSError:
                pass
        logger(f"[{input_mp3}] 码率/采样率提升失败: {e}")
```

Change `add_bgm` signature and replace its `print` calls:

```python
def add_bgm(
    main_audio: str,
    bgm_audio: str,
    main_volume: float = 1.0,
    bgm_volume: float = 0.25,
    loop_bgm: bool = True,
    logger: Callable[[str], None] = print,
):
```

Inside `add_bgm`, replace every `print(...)` with `logger(...)`. For multi-argument calls, format them as one string, for example:

```python
logger(f"返回码: {e.returncode}")
logger(f"错误输出 (stderr):\n{e.stderr}")
```

- [ ] **Step 4: Update converter initialization**

In `src/epub2mp3/main.py`, update imports:

```python
import asyncio
import argparse
import os
import random
import tempfile
from collections.abc import Callable
```

Replace `EpubToMP3Converter.__init__` with:

```python
    def __init__(
        self,
        voice: str,
        output_dir: str,
        max_retries: int = 3,
        bg_dir=None,
        max_concurrency: int = 3,
        enable_high_quality: bool = True,
        enable_lyrics: bool = True,
        logger: Callable[[str], None] = print,
    ):
        self.voice = voice
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.max_concurrency = max_concurrency
        self.enable_high_quality = enable_high_quality
        self.enable_lyrics = enable_lyrics
        self.log = logger
        self.bg_files = None
        if bg_dir and os.path.isdir(bg_dir):
            self.bg_files = [
                os.path.join(bg_dir, f)
                for f in os.listdir(bg_dir)
                if os.path.isfile(os.path.join(bg_dir, f))
                and f.lower().endswith(".mp3")
            ]
        ensure_output_dir(output_dir)
```

- [ ] **Step 5: Replace converter print calls with injected logging**

In `text_to_speech_with_retry`, replace each `print(...)` with `self.log(...)`.

The method should read:

```python
    async def text_to_speech_with_retry(self, text: str, output_file: str) -> None:
        """将文本转换为语音，带重试机制"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                self.log(f"[{output_file}] Attempt {attempt + 1}/{self.max_retries}")
                communicate = edge_tts.Communicate(text, self.voice)
                await communicate.save(output_file)
                self.log(f"[{output_file}] Conversion successful")
                return

            except Exception as e:
                last_exception = e
                self.log(f"[{output_file}] Attempt {attempt + 1} failed: {str(e)}")

            if attempt < self.max_retries - 1:
                wait_time = 2**attempt
                self.log(f"[{output_file}] Waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

        self.log(f"[{output_file}] All attempts failed")
        raise last_exception
```

- [ ] **Step 6: Add bounded concurrency to `convert_epub`**

Replace `convert_epub` with:

```python
    async def convert_epub(self, epub_path: str) -> None:
        """转换 EPUB 文件为 MP3"""
        if not os.path.exists(epub_path):
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        chapters = get_chapters(epub_path)
        tasks = []
        failed_chapters = []
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def run_chapter(
            index: int,
            title: str,
            content: str,
            output_path: str,
        ) -> None:
            async with semaphore:
                await self.process_chapter(
                    index,
                    title,
                    content,
                    output_path,
                    failed_chapters,
                )

        for i, (title, content) in enumerate(chapters, 1):
            safe_title = sanitize_filename(title)
            filename = f"{i:03d}_{safe_title}.mp3"
            output_path = os.path.join(self.output_dir, filename)

            self.log(f"Processing chapter {i}: {title}")

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.log(f"Chapter {i} already exists, skipping...")
                continue

            task = asyncio.create_task(run_chapter(i, title, content, output_path))
            tasks.append(task)

        await asyncio.gather(*tasks)

        if failed_chapters:
            self.log("\nThe following chapters failed to convert:")
            for chapter in failed_chapters:
                self.log(f"- Chapter {chapter}")
```

- [ ] **Step 7: Add post-processing toggles and temp-file cleanup**

Replace `process_chapter` with:

```python
    async def process_chapter(
        self,
        index: int,
        title: str,
        content: str,
        output_path: str,
        failed_chapters: list,
    ) -> None:
        """处理单个章节的转换，包含错误处理"""
        temp_output = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                temp_output = tmp_file.name

            await self.text_to_speech_with_retry(content, temp_output)
            if self.bg_files and len(self.bg_files) > 0:
                bg_path = random.choice(self.bg_files)
                add_bgm(temp_output, bg_path, logger=self.log)
            if self.enable_high_quality:
                convert_mp3_high_quality(temp_output, logger=self.log)
            if self.enable_lyrics:
                write_lyrics_to_mp3(temp_output, content, logger=self.log)

            os.replace(temp_output, output_path)
            temp_output = None

            self.log(f"Successfully converted chapter {index}: {title}")
        except Exception as e:
            self.log(f"Failed to convert chapter {index}: {title}")
            self.log(f"Error: {str(e)}")
            failed_chapters.append(index)
        finally:
            if temp_output and os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except OSError as cleanup_error:
                    self.log(f"Failed to remove temporary file {temp_output}: {cleanup_error}")
```

- [ ] **Step 8: Run the converter tests**

Run:

```shell
pdm run python -m unittest tests.test_converter_options -v
```

Expected: PASS.

- [ ] **Step 9: Run existing helper tests**

Run:

```shell
pdm run python -m unittest tests.test_options tests.test_voices -v
```

Expected: PASS.

- [ ] **Step 10: Checkpoint**

Record changed files:

```text
src/epub2mp3/main.py
src/epub2mp3/utils.py
tests/test_converter_options.py
```

---

### Task 4: CLI Parser and Shared Validation

**Files:**
- Modify: `src/epub2mp3/main.py`
- Test: `tests/test_cli_parser.py`

- [ ] **Step 1: Write failing CLI parser tests**

Create `tests/test_cli_parser.py`:

```python
import unittest

from epub2mp3.main import build_parser


class CliParserTests(unittest.TestCase):
    def test_parser_accepts_speed_and_post_processing_flags(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "book.epub",
                "--concurrency",
                "4",
                "--no-high-quality",
                "--no-lyrics",
                "-b",
                "bg",
            ]
        )

        self.assertEqual(args.epub_path, "book.epub")
        self.assertEqual(args.concurrency, 4)
        self.assertTrue(args.no_high_quality)
        self.assertTrue(args.no_lyrics)
        self.assertEqual(args.bg_dir, "bg")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the parser test to verify it fails**

Run:

```shell
pdm run python -m unittest tests.test_cli_parser -v
```

Expected: FAIL or ERROR with `ImportError` for missing `build_parser`.

- [ ] **Step 3: Add parser construction and new CLI flags**

In `src/epub2mp3/main.py`, import shared option helpers:

```python
from .options import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RETRIES,
    DEFAULT_VOICE,
    ConversionOptions,
    validate_conversion_inputs,
)
```

Add this function above `main()`:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将 EPUB 电子书转换为 MP3 音频文件，每章一个文件。",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("epub_path", type=str, help="要转换的 EPUB 文件的路径。")

    parser.add_argument(
        "-v",
        "--voice",
        type=str,
        default=DEFAULT_VOICE,
        help=(
            "用于文本转语音的 Edge TTS 声音。\n"
            "例如: zh-CN-YunxiNeural, en-US-AriaNeural\n"
            "使用 'edge-tts --list-voices' 命令查看所有可用声音。\n"
            f"默认值: {DEFAULT_VOICE}"
        ),
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"保存生成的 MP3 文件的目录。\n默认值: {DEFAULT_OUTPUT_DIR}",
    )

    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"转换失败时的最大重试次数。\n默认值: {DEFAULT_RETRIES}",
    )

    parser.add_argument(
        "-b",
        "--bg-dir",
        type=str,
        help="背景音乐文件所在目录，如果指定，程序会随机选择一个背景音乐添加到每个章节的音频中。\n默认不添加背景音乐。",
    )

    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=DEFAULT_MAX_CONCURRENCY,
        help=f"同时转换的最大章节数。\n默认值: {DEFAULT_MAX_CONCURRENCY}",
    )

    parser.add_argument(
        "--no-high-quality",
        action="store_true",
        help="跳过 320kbps/48kHz 高质量转码，加快转换速度。",
    )

    parser.add_argument(
        "--no-lyrics",
        action="store_true",
        help="跳过歌词标签写入，加快转换速度。",
    )

    return parser
```

- [ ] **Step 4: Replace `main()` parser setup and fix `bg_dir` usage**

Replace the start of `main()` through converter creation with:

```python
def main():
    parser = build_parser()
    args = parser.parse_args()

    options = ConversionOptions(
        epub_path=args.epub_path,
        output_dir=args.output_dir,
        voice=args.voice,
        retries=args.retries,
        bg_dir=args.bg_dir,
        max_concurrency=args.concurrency,
        enable_high_quality=not args.no_high_quality,
        enable_lyrics=not args.no_lyrics,
    )

    validation_errors = validate_conversion_inputs(options)
    if validation_errors:
        for error in validation_errors:
            print(f"错误: {error}")
        return

    converter = EpubToMP3Converter(
        voice=options.voice,
        output_dir=options.output_dir,
        max_retries=options.retries,
        bg_dir=options.bg_dir,
        max_concurrency=options.max_concurrency,
        enable_high_quality=options.enable_high_quality,
        enable_lyrics=options.enable_lyrics,
    )
```

Keep the existing `try` block below converter creation, but call:

```python
asyncio.run(converter.convert_epub(options.epub_path))
print(f"所有音频文件已保存到目录: {os.path.abspath(options.output_dir)}")
```

- [ ] **Step 5: Remove the old inline parser block**

Delete the old repeated `parser.add_argument(...)` block from `main()` after confirming `build_parser()` contains all arguments.

- [ ] **Step 6: Run parser tests**

Run:

```shell
pdm run python -m unittest tests.test_cli_parser -v
```

Expected: PASS.

- [ ] **Step 7: Run converter and validation tests**

Run:

```shell
pdm run python -m unittest tests.test_options tests.test_converter_options -v
```

Expected: PASS.

- [ ] **Step 8: Checkpoint**

Record changed files:

```text
src/epub2mp3/main.py
tests/test_cli_parser.py
```

---

### Task 5: Tkinter GUI Entry Point

**Files:**
- Create: `src/epub2mp3/gui.py`
- Test: `tests/test_gui_import.py`

- [ ] **Step 1: Write the failing GUI import test**

Create `tests/test_gui_import.py`:

```python
import importlib
import unittest


class GuiImportTests(unittest.TestCase):
    def test_gui_module_exposes_launch_function_without_creating_window(self):
        module = importlib.import_module("epub2mp3.gui")

        self.assertTrue(callable(module.main))
        self.assertTrue(hasattr(module, "Epub2Mp3App"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the GUI import test to verify it fails**

Run:

```shell
pdm run python -m unittest tests.test_gui_import -v
```

Expected: FAIL or ERROR with `ModuleNotFoundError: No module named 'epub2mp3.gui'`.

- [ ] **Step 3: Add the Tkinter GUI module**

Create `src/epub2mp3/gui.py`:

```python
import asyncio
import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from .main import EpubToMP3Converter
from .options import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RETRIES,
    DEFAULT_VOICE,
    ConversionOptions,
    validate_conversion_inputs,
)
from .voices import COMMON_VOICES, fetch_edge_tts_voice_names


class Epub2Mp3App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("epub2mp3")
        self.root.geometry("980x620")
        self.root.minsize(860, 520)
        self.is_running = False

        self.epub_path_var = tk.StringVar()
        self.voice_var = tk.StringVar(value=DEFAULT_VOICE)
        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.bg_dir_var = tk.StringVar()
        self.retries_var = tk.StringVar(value=str(DEFAULT_RETRIES))
        self.concurrency_var = tk.StringVar(value=str(DEFAULT_MAX_CONCURRENCY))
        self.enable_high_quality_var = tk.BooleanVar(value=True)
        self.enable_lyrics_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        settings = ttk.Frame(self.root, padding=16)
        settings.grid(row=0, column=0, sticky="ns")

        log_frame = ttk.Frame(self.root, padding=(0, 16, 16, 16))
        log_frame.grid(row=0, column=1, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        ttk.Label(settings, text="转换设置", font=("", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        self._add_file_row(settings, 1, "EPUB 文件", self.epub_path_var, self.browse_epub)

        ttk.Label(settings, text="音色").grid(row=2, column=0, sticky="w", pady=(10, 4))
        self.voice_combo = ttk.Combobox(
            settings,
            textvariable=self.voice_var,
            values=COMMON_VOICES,
            width=34,
        )
        self.voice_combo.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Button(settings, text="刷新音色", command=self.refresh_voices).grid(
            row=3, column=2, padx=(8, 0), sticky="ew"
        )

        self._add_file_row(
            settings,
            4,
            "输出目录",
            self.output_dir_var,
            self.browse_output_dir,
        )
        self._add_file_row(
            settings,
            7,
            "背景音乐目录",
            self.bg_dir_var,
            self.browse_bg_dir,
            allow_clear=True,
        )

        ttk.Label(settings, text="重试次数").grid(row=10, column=0, sticky="w", pady=(10, 4))
        ttk.Spinbox(settings, from_=1, to=20, textvariable=self.retries_var, width=8).grid(
            row=11, column=0, sticky="w"
        )

        ttk.Label(settings, text="并发章节数").grid(row=10, column=1, sticky="w", pady=(10, 4))
        ttk.Spinbox(
            settings,
            from_=1,
            to=10,
            textvariable=self.concurrency_var,
            width=8,
        ).grid(row=11, column=1, sticky="w")

        ttk.Checkbutton(
            settings,
            text="高质量转码",
            variable=self.enable_high_quality_var,
        ).grid(row=12, column=0, columnspan=3, sticky="w", pady=(14, 0))

        ttk.Checkbutton(
            settings,
            text="写入歌词标签",
            variable=self.enable_lyrics_var,
        ).grid(row=13, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.start_button = ttk.Button(settings, text="开始转换", command=self.start_conversion)
        self.start_button.grid(row=14, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        ttk.Label(log_frame, text="转换日志", font=("", 13, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.log_text = tk.Text(log_frame, wrap="word", state="disabled")
        self.log_text.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _add_file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_command,
        allow_clear: bool = False,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(10, 4))
        ttk.Entry(parent, textvariable=variable, width=38).grid(
            row=row + 1, column=0, columnspan=2, sticky="ew"
        )
        ttk.Button(parent, text="浏览", command=browse_command).grid(
            row=row + 1, column=2, padx=(8, 0), sticky="ew"
        )
        if allow_clear:
            ttk.Button(parent, text="清空", command=lambda: variable.set("")).grid(
                row=row + 2, column=2, padx=(8, 0), pady=(6, 0), sticky="ew"
            )

    def browse_epub(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 EPUB 文件",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")],
        )
        if path:
            self.epub_path_var.set(path)

    def browse_output_dir(self) -> None:
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)

    def browse_bg_dir(self) -> None:
        path = filedialog.askdirectory(title="选择背景音乐目录")
        if path:
            self.bg_dir_var.set(path)

    def append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def thread_safe_log(self, message: str) -> None:
        self.root.after(0, self.append_log, message)

    def refresh_voices(self) -> None:
        if self.is_running:
            self.append_log("转换运行中，暂不能刷新音色。")
            return
        self.append_log("正在刷新音色列表...")
        threading.Thread(target=self._refresh_voices_worker, daemon=True).start()

    def _refresh_voices_worker(self) -> None:
        try:
            voices = asyncio.run(fetch_edge_tts_voice_names())
        except Exception as exc:
            self.thread_safe_log(f"刷新音色失败: {exc}")
            return

        def apply_voices() -> None:
            self.voice_combo.configure(values=voices)
            if self.voice_var.get() not in voices and voices:
                self.voice_var.set(voices[0])
            self.append_log(f"音色列表已刷新，共 {len(voices)} 个。")

        self.root.after(0, apply_voices)

    def start_conversion(self) -> None:
        if self.is_running:
            self.append_log("转换已经在运行中。")
            return

        try:
            retries = int(self.retries_var.get())
            concurrency = int(self.concurrency_var.get())
        except ValueError:
            self.append_log("错误: 重试次数和并发章节数必须是整数。")
            return

        options = ConversionOptions(
            epub_path=self.epub_path_var.get().strip(),
            output_dir=self.output_dir_var.get().strip(),
            voice=self.voice_var.get().strip(),
            retries=retries,
            bg_dir=self.bg_dir_var.get().strip() or None,
            max_concurrency=concurrency,
            enable_high_quality=self.enable_high_quality_var.get(),
            enable_lyrics=self.enable_lyrics_var.get(),
        )
        errors = validate_conversion_inputs(options)
        if errors:
            for error in errors:
                self.append_log(f"错误: {error}")
            return

        self.is_running = True
        self.start_button.configure(state="disabled")
        self.append_log("开始转换...")
        threading.Thread(target=self._conversion_worker, args=(options,), daemon=True).start()

    def _conversion_worker(self, options: ConversionOptions) -> None:
        try:
            converter = EpubToMP3Converter(
                voice=options.voice,
                output_dir=options.output_dir,
                max_retries=options.retries,
                bg_dir=options.bg_dir,
                max_concurrency=options.max_concurrency,
                enable_high_quality=options.enable_high_quality,
                enable_lyrics=options.enable_lyrics,
                logger=self.thread_safe_log,
            )
            asyncio.run(converter.convert_epub(options.epub_path))
            self.thread_safe_log("转换完成！")
            self.thread_safe_log(f"所有音频文件已保存到目录: {os.path.abspath(options.output_dir)}")
        except Exception as exc:
            self.thread_safe_log(f"转换过程中出现错误: {exc}")
        finally:
            self.root.after(0, self._conversion_finished)

    def _conversion_finished(self) -> None:
        self.is_running = False
        self.start_button.configure(state="normal")


def main() -> None:
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    root = tk.Tk()
    Epub2Mp3App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the GUI import test**

Run:

```shell
pdm run python -m unittest tests.test_gui_import -v
```

Expected: PASS.

- [ ] **Step 5: Run all unit tests added so far**

Run:

```shell
pdm run python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 6: Checkpoint**

Record changed files:

```text
src/epub2mp3/gui.py
tests/test_gui_import.py
```

---

### Task 6: PDM Script and README Updates

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`

- [ ] **Step 1: Add the GUI script**

In `pyproject.toml`, update `[tool.pdm.scripts]`:

```toml
[tool.pdm.scripts]
start = "python -m epub2mp3.main"
gui = "python -m epub2mp3.gui"
```

- [ ] **Step 2: Update README help text**

In `README.md`, update the help block to include:

```text
  -c CONCURRENCY, --concurrency CONCURRENCY
                        同时转换的最大章节数。
                        默认值: 3
  --no-high-quality     跳过 320kbps/48kHz 高质量转码，加快转换速度。
  --no-lyrics           跳过歌词标签写入，加快转换速度。
```

- [ ] **Step 3: Add GUI usage documentation**

Add this section after the CLI help section:

````markdown
## 桌面界面

源码运行版桌面界面：

```shell
pdm gui
```

界面支持选择 EPUB 文件、音色、输出目录、背景音乐目录、重试次数、并发章节数，并可以关闭高质量转码或歌词写入来加快转换。
````

- [ ] **Step 4: Fix the background music example**

Replace:

```shell
pdm start -b bg -o zh-CN-YunjianNeural example/mc.epub
```

With:

```shell
pdm start -b bg -v zh-CN-YunjianNeural example/mc.epub
```

- [ ] **Step 5: Verify the PDM script is registered**

Run:

```shell
pdm run python -m epub2mp3.gui
```

Expected: A Tkinter window opens. Close the window manually after confirming it launches.

If the environment cannot show GUI windows, run:

```shell
pdm run python -m unittest tests.test_gui_import -v
```

Expected: PASS.

- [ ] **Step 6: Checkpoint**

Record changed files:

```text
pyproject.toml
README.md
```

---

### Task 7: Final Verification

**Files:**
- Verify all files changed by Tasks 1-6.

- [ ] **Step 1: Run full unit test suite**

Run:

```shell
pdm run python -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 2: Verify CLI help**

Run:

```shell
pdm start -h
```

Expected: Help output includes `--concurrency`, `--no-high-quality`, and `--no-lyrics`.

- [ ] **Step 3: Verify GUI import remains side-effect free**

Run:

```shell
pdm run python -c "import epub2mp3.gui; print('ok')"
```

Expected output:

```text
ok
```

- [ ] **Step 4: Verify GUI launch when a desktop is available**

Run:

```shell
pdm gui
```

Expected: The desktop window opens with settings on the left and logs on the right.

- [ ] **Step 5: Optional smoke test with the example EPUB**

Run only if network access to Edge TTS is available:

```shell
pdm start --concurrency 1 --no-high-quality --no-lyrics -o output_audio_smoke example/mc.epub
```

Expected: MP3 files are created under `output_audio_smoke`.

- [ ] **Step 6: Final checkpoint**

Record final changed files:

```text
README.md
pyproject.toml
src/epub2mp3/gui.py
src/epub2mp3/main.py
src/epub2mp3/options.py
src/epub2mp3/utils.py
src/epub2mp3/voices.py
tests/test_cli_parser.py
tests/test_converter_options.py
tests/test_gui_import.py
tests/test_options.py
tests/test_voices.py
```
