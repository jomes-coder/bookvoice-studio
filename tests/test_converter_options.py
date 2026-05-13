import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bookvoice.book import BookMetadata, ParsedBook, ParsedChapter
from bookvoice.converter import (
    CHAPTER_STATUS_CANCELED,
    CHAPTER_STATUS_COMPLETED,
    CHAPTER_STATUS_FAILED,
    CHAPTER_STATUS_RUNNING,
    CHAPTER_STATUS_SKIPPED,
    ConversionResult,
    EpubToMP3Converter,
)


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


class PausingConverter(EpubToMP3Converter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []

    async def process_chapter(self, index, title, content, output_path, failed_chapters):
        self.started.append(index)
        await asyncio.sleep(0.01)


class RecordingPathConverter(EpubToMP3Converter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_paths = []

    async def process_chapter(self, index, title, content, output_path, failed_chapters):
        self.output_paths.append(output_path)


class CancelAfterFirstChapterConverter(EpubToMP3Converter):
    def __init__(self, cancel_state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancel_state = cancel_state
        self.started = []

    async def process_chapter(self, index, title, content, output_path, failed_chapters):
        self.started.append(index)
        self.cancel_state["cancel"] = True


class ConverterOptionsTests(unittest.TestCase):
    def parsed_book_with_chapters(self, chapters):
        return ParsedBook(
            metadata=BookMetadata(title="测试书", author="作者"),
            chapters=[
                ParsedChapter(
                    index=index,
                    title=title,
                    text=content,
                    source_id=f"{index}.xhtml",
                )
                for index, (title, content) in enumerate(chapters, 1)
            ],
        )

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

            with patch(
                "bookvoice.converter.parse_book",
                return_value=self.parsed_book_with_chapters(chapters),
            ):
                asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertLessEqual(converter.max_seen, 2)

    def test_convert_epub_passes_configured_ebook_convert_path_to_parser(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mobi_path = root / "book.mobi"
            mobi_path.write_text("placeholder", encoding="utf-8")
            configured_converter = "D:\\Calibre\\ebook-convert.exe"
            parsed = self.parsed_book_with_chapters([("第一章", "content")])

            converter = RecordingPathConverter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                ebook_convert_path=configured_converter,
                logger=lambda message: None,
            )

            with patch("bookvoice.converter.parse_book", return_value=parsed) as parser:
                asyncio.run(converter.convert_epub(str(mobi_path)))

            parser.assert_called_once_with(
                str(mobi_path),
                calibre_converter=configured_converter,
            )

    def test_convert_epub_writes_chapters_under_book_title_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = ParsedBook(
                metadata=BookMetadata(title='测试<书>', author="作者"),
                chapters=[
                    ParsedChapter(
                        index=1,
                        title="第一章",
                        text="content",
                        source_id="chapter.xhtml",
                    )
                ],
            )

            converter = RecordingPathConverter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                logger=lambda message: None,
            )

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                result = asyncio.run(converter.convert_epub(str(epub_path)))

            expected_dir = root / "out" / "测试书"
            self.assertEqual(Path(converter.output_paths[0]).parent, expected_dir)
            self.assertEqual(Path(converter.actual_output_dir), expected_dir)
            self.assertIsInstance(result, ConversionResult)
            self.assertEqual(result.total, 1)
            self.assertEqual(result.completed, 1)
            self.assertEqual(result.failed, 0)
            self.assertEqual(result.skipped, 0)
            self.assertEqual(Path(result.output_dir), expected_dir)
            self.assertEqual(Path(result.summary_path), expected_dir / "conversion_summary.json")

    def test_convert_epub_writes_conversion_summary_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = ParsedBook(
                metadata=BookMetadata(title="测试书", author="作者", language="zh-CN"),
                chapters=[
                    ParsedChapter(
                        index=1,
                        title="第一章",
                        text="content",
                        source_id="chapter.xhtml",
                    )
                ],
                source_path=str(epub_path),
            )

            converter = RecordingPathConverter(
                voice="zh-CN-XiaoxiaoNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                max_concurrency=2,
                enable_high_quality=False,
                enable_lyrics=False,
                rate="+15%",
                volume="+10%",
                pitch="+0Hz",
                logger=lambda message: None,
            )

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                result = asyncio.run(converter.convert_epub(str(epub_path)))

            summary_path = Path(result.summary_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

            self.assertEqual(summary_path.parent, Path(result.output_dir))
            self.assertEqual(summary["source_path"], str(epub_path))
            self.assertEqual(summary["book"]["title"], "测试书")
            self.assertEqual(summary["book"]["author"], "作者")
            self.assertEqual(summary["book"]["language"], "zh-CN")
            self.assertEqual(summary["result"]["total"], 1)
            self.assertEqual(summary["result"]["completed"], 1)
            self.assertEqual(summary["result"]["failed"], 0)
            self.assertEqual(summary["options"]["voice"], "zh-CN-XiaoxiaoNeural")
            self.assertEqual(summary["options"]["rate"], "+15%")
            self.assertFalse(summary["options"]["enable_high_quality"])

    def test_convert_epub_result_counts_skipped_and_failed_chapters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = ParsedBook(
                metadata=BookMetadata(title="测试书", author="作者"),
                chapters=[
                    ParsedChapter(index=1, title="已存在", text="content", source_id="1.xhtml"),
                    ParsedChapter(index=2, title="会失败", text="content", source_id="2.xhtml"),
                ],
            )
            existing_dir = root / "out" / "测试书"
            existing_dir.mkdir(parents=True)
            (existing_dir / "001_已存在.mp3").write_bytes(b"mp3")

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                logger=lambda message: None,
            )

            async def fail_chapter(index, title, content, output_path, failed_chapters):
                failed_chapters.append(index)

            converter.process_chapter = fail_chapter

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                result = asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertEqual(result.total, 2)
            self.assertEqual(result.completed, 0)
            self.assertEqual(result.failed, 1)
            self.assertEqual(result.skipped, 1)
            self.assertEqual(result.failed_chapters, [2])

    def test_convert_epub_emits_chapter_status_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = ParsedBook(
                metadata=BookMetadata(title="测试书", author="作者"),
                chapters=[
                    ParsedChapter(index=1, title="已存在", text="content", source_id="1.xhtml"),
                    ParsedChapter(index=2, title="成功", text="content", source_id="2.xhtml"),
                    ParsedChapter(index=3, title="失败", text="content", source_id="3.xhtml"),
                ],
            )
            existing_dir = root / "out" / "测试书"
            existing_dir.mkdir(parents=True)
            (existing_dir / "001_已存在.mp3").write_bytes(b"mp3")
            events = []

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                max_concurrency=1,
                logger=lambda message: None,
                chapter_status_callback=events.append,
            )

            async def process_chapter(index, title, content, output_path, failed_chapters):
                if index == 3:
                    failed_chapters.append(index)

            converter.process_chapter = process_chapter

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertEqual(
                [(event["index"], event["status"]) for event in events],
                [
                    (1, CHAPTER_STATUS_SKIPPED),
                    (2, CHAPTER_STATUS_RUNNING),
                    (2, CHAPTER_STATUS_COMPLETED),
                    (3, CHAPTER_STATUS_RUNNING),
                    (3, CHAPTER_STATUS_FAILED),
                ],
            )

    def test_convert_epub_overwrites_existing_chapter_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = ParsedBook(
                metadata=BookMetadata(title="测试书", author="作者"),
                chapters=[
                    ParsedChapter(index=1, title="已存在", text="content", source_id="1.xhtml"),
                ],
            )
            existing_dir = root / "out" / "测试书"
            existing_dir.mkdir(parents=True)
            existing_file = existing_dir / "001_已存在.mp3"
            existing_file.write_bytes(b"old")

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                overwrite_existing=True,
                logger=lambda message: None,
            )
            processed = []

            async def process_chapter(index, title, content, output_path, failed_chapters):
                processed.append((index, title, output_path))
                Path(output_path).write_bytes(b"new")

            converter.process_chapter = process_chapter

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                result = asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertEqual(processed, [(1, "已存在", str(existing_file))])
            self.assertEqual(result.completed, 1)
            self.assertEqual(result.skipped, 0)
            self.assertEqual(existing_file.read_bytes(), b"new")

    def test_convert_epub_only_processes_selected_chapters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = self.parsed_book_with_chapters(
                [
                    ("第一章", "content"),
                    ("第二章", "content"),
                    ("第三章", "content"),
                ]
            )

            converter = RecordingPathConverter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                selected_chapter_indexes=(2,),
                logger=lambda message: None,
            )

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                result = asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertEqual(result.total, 1)
            self.assertEqual(len(converter.output_paths), 1)
            self.assertEqual(Path(converter.output_paths[0]).name, "002_第二章.mp3")

    def test_convert_epub_cancels_pending_chapters_after_current_chapter_finishes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            cancel_state = {"cancel": False}
            parsed = self.parsed_book_with_chapters(
                [
                    ("第一章", "content"),
                    ("第二章", "content"),
                    ("第三章", "content"),
                ]
            )

            converter = CancelAfterFirstChapterConverter(
                cancel_state,
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                max_concurrency=1,
                cancel_checker=lambda: cancel_state["cancel"],
                logger=lambda message: None,
            )

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                result = asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertEqual(converter.started, [1])
            self.assertTrue(result.canceled)
            self.assertEqual(result.canceled_count, 2)
            self.assertEqual(result.completed, 1)

    def test_convert_epub_emits_canceled_status_for_pending_chapters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            cancel_state = {"cancel": False}
            events = []
            parsed = self.parsed_book_with_chapters(
                [
                    ("第一章", "content"),
                    ("第二章", "content"),
                ]
            )

            converter = CancelAfterFirstChapterConverter(
                cancel_state,
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                max_concurrency=1,
                cancel_checker=lambda: cancel_state["cancel"],
                logger=lambda message: None,
                chapter_status_callback=events.append,
            )

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                asyncio.run(converter.convert_epub(str(epub_path)))

            self.assertIn(
                {"index": 2, "title": "第二章", "status": CHAPTER_STATUS_CANCELED},
                events,
            )

    def test_convert_epub_waits_for_pause_before_starting_chapters(self):
        async def run_test():
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                epub_path = root / "book.epub"
                epub_path.write_text("placeholder", encoding="utf-8")
                pause_released = asyncio.Event()

                async def pause_waiter():
                    await pause_released.wait()

                converter = PausingConverter(
                    voice="zh-CN-YunxiaNeural",
                    output_dir=str(root / "out"),
                    max_retries=3,
                    max_concurrency=2,
                    logger=lambda message: None,
                    pause_waiter=pause_waiter,
                )
                chapters = [(f"Chapter {i}", "content") for i in range(3)]

                with patch(
                    "bookvoice.converter.parse_book",
                    return_value=self.parsed_book_with_chapters(chapters),
                ):
                    conversion = asyncio.create_task(converter.convert_epub(str(epub_path)))
                    await asyncio.sleep(0.05)

                    self.assertEqual(converter.started, [])

                    pause_released.set()
                    await asyncio.wait_for(conversion, timeout=1)

                self.assertEqual(converter.started, [1, 2, 3])

        asyncio.run(run_test())

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

            with patch("bookvoice.converter.convert_mp3_high_quality") as transcode:
                with patch("bookvoice.converter.write_lyrics_to_mp3") as lyrics:
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

    def test_text_to_speech_passes_speech_parameters_to_edge_tts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "chapter.mp3"
            calls = []

            class FakeCommunicate:
                def __init__(self, text, voice, **kwargs):
                    calls.append((text, voice, kwargs))

                async def save(self, output_file):
                    Path(output_file).write_bytes(b"mp3")

            converter = EpubToMP3Converter(
                voice="zh-CN-XiaoxiaoNeural",
                output_dir=str(Path(temp_dir) / "out"),
                max_retries=1,
                rate="+15%",
                volume="+5%",
                pitch="+2Hz",
                logger=lambda message: None,
            )

            with patch("bookvoice.converter.edge_tts.Communicate", FakeCommunicate):
                asyncio.run(
                    converter.text_to_speech_with_retry(
                        "测试文本",
                        str(output_path),
                    )
                )

            self.assertEqual(
                calls,
                [
                    (
                        "测试文本",
                        "zh-CN-XiaoxiaoNeural",
                        {"rate": "+15%", "volume": "+5%", "pitch": "+2Hz"},
                    )
                ],
            )

    def test_process_chapter_creates_temporary_file_in_output_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "out"
            output_path = output_dir / "chapter.mp3"
            tts_paths = []

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(output_dir),
                max_retries=3,
                enable_high_quality=False,
                enable_lyrics=False,
                logger=lambda message: None,
            )

            async def fake_tts(text, output_file):
                tts_paths.append(Path(output_file))
                Path(output_file).write_bytes(b"mp3")

            converter.text_to_speech_with_retry = fake_tts

            asyncio.run(
                converter.process_chapter(
                    1,
                    "Chapter",
                    "content",
                    str(output_path),
                    [],
                )
            )

            self.assertEqual(len(tts_paths), 1)
            self.assertEqual(tts_paths[0].parent.resolve(), output_dir.resolve())
            self.assertTrue(output_path.exists())

    def test_process_chapter_writes_mp3_metadata_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "chapter.mp3"
            cover_path = root / "cover.jpg"
            cover_path.write_bytes(b"cover")

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                enable_high_quality=False,
                enable_lyrics=False,
                enable_mp3_metadata=True,
                cover_path=str(cover_path),
                logger=lambda message: None,
            )
            converter.book_title = "测试书"
            converter.book_author = "作者"

            async def fake_tts(text, output_file):
                Path(output_file).write_bytes(b"mp3")

            converter.text_to_speech_with_retry = fake_tts

            with patch("bookvoice.converter.write_mp3_chapter_metadata") as metadata:
                asyncio.run(
                    converter.process_chapter(
                        1,
                        "第一章",
                        "content",
                        str(output_path),
                        [],
                    )
                )

            metadata.assert_called_once_with(
                str(output_path),
                book_title="测试书",
                author="作者",
                chapter_title="第一章",
                chapter_index=1,
                cover_path=str(cover_path),
                logger=converter.log,
            )

    def test_convert_epub_builds_m4b_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            parsed = self.parsed_book_with_chapters(
                [
                    ("第一章", "content"),
                    ("第二章", "content"),
                ]
            )

            converter = EpubToMP3Converter(
                voice="zh-CN-YunxiaNeural",
                output_dir=str(root / "out"),
                max_retries=3,
                enable_high_quality=False,
                enable_lyrics=False,
                export_m4b=True,
                logger=lambda message: None,
            )

            async def write_chapter(index, title, content, output_path, failed_chapters):
                Path(output_path).write_bytes(b"mp3")

            converter.process_chapter = write_chapter

            with patch("bookvoice.converter.parse_book", return_value=parsed):
                with patch(
                    "bookvoice.converter.build_m4b_audiobook",
                    return_value=str(root / "out" / "测试书" / "测试书.m4b"),
                ) as build_m4b:
                    result = asyncio.run(converter.convert_epub(str(epub_path)))

            build_m4b.assert_called_once()
            m4b_chapters = build_m4b.call_args.kwargs["chapters"]
            self.assertEqual([chapter.title for chapter in m4b_chapters], ["第一章", "第二章"])
            self.assertEqual(result.m4b_path, str(root / "out" / "测试书" / "测试书.m4b"))


if __name__ == "__main__":
    unittest.main()


