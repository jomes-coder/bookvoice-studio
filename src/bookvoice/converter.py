import asyncio
import argparse
import os
import random
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
import sys

import edge_tts

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "bookvoice"

from .utils import (
    sanitize_filename,
    ensure_output_dir,
    write_lyrics_to_mp3,
    convert_mp3_high_quality,
    add_bgm,
)
from .audio_product import M4BChapter, build_m4b_audiobook, write_mp3_chapter_metadata
from .book import build_book_output_dir, parse_book
from .conversion_summary import write_conversion_summary
from .health import format_health_checks, run_environment_checks
from .options import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_RETRIES,
    DEFAULT_VOLUME,
    DEFAULT_VOICE,
    ConversionOptions,
    validate_conversion_inputs,
)


CHAPTER_STATUS_RUNNING = "running"
CHAPTER_STATUS_COMPLETED = "completed"
CHAPTER_STATUS_FAILED = "failed"
CHAPTER_STATUS_SKIPPED = "skipped"
CHAPTER_STATUS_CANCELED = "canceled"


@dataclass(frozen=True)
class ConversionResult:
    total: int
    completed: int
    failed: int
    skipped: int
    failed_chapters: list[int]
    output_dir: str
    canceled: bool = False
    canceled_count: int = 0
    m4b_path: str | None = None
    summary_path: str | None = None


class EpubToMP3Converter:
    def __init__(
        self,
        voice: str,
        output_dir: str,
        max_retries: int = 3,
        bg_dir=None,
        max_concurrency: int = 3,
        enable_high_quality: bool = True,
        enable_lyrics: bool = True,
        rate: str = DEFAULT_RATE,
        volume: str = DEFAULT_VOLUME,
        pitch: str = DEFAULT_PITCH,
        selected_chapter_indexes: tuple[int, ...] | None = None,
        cover_path: str | None = None,
        enable_mp3_metadata: bool = True,
        export_m4b: bool = False,
        overwrite_existing: bool = False,
        ebook_convert_path: str | None = None,
        logger: Callable[[str], None] = print,
        pause_waiter: Callable[[], Awaitable[None]] | None = None,
        cancel_checker: Callable[[], bool] | None = None,
        progress_callback: Callable[[dict[str, int | str]], None] | None = None,
        chapter_status_callback: Callable[[dict[str, int | str]], None] | None = None,
    ):
        self.voice = voice
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.max_concurrency = max_concurrency
        self.enable_high_quality = enable_high_quality
        self.enable_lyrics = enable_lyrics
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.selected_chapter_indexes = selected_chapter_indexes
        self.cover_path = cover_path
        self.enable_mp3_metadata = enable_mp3_metadata
        self.export_m4b = export_m4b
        self.overwrite_existing = overwrite_existing
        self.ebook_convert_path = ebook_convert_path
        self.log = logger
        self.pause_waiter = pause_waiter
        self.cancel_checker = cancel_checker
        self.progress_callback = progress_callback
        self.chapter_status_callback = chapter_status_callback
        self.actual_output_dir = output_dir
        self.book_title = ""
        self.book_author = ""
        self.bg_files = None
        if bg_dir and os.path.isdir(bg_dir):
            self.bg_files = [
                os.path.join(bg_dir, f)
                for f in os.listdir(bg_dir)
                if os.path.isfile(os.path.join(bg_dir, f))
                and f.lower().endswith(".mp3")
            ]
        ensure_output_dir(output_dir)

    async def text_to_speech_with_retry(self, text: str, output_file: str) -> None:
        """将文本转换为语音，带重试机制"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                self.log(f"[{output_file}] Attempt {attempt + 1}/{self.max_retries}")
                communicate = edge_tts.Communicate(
                    text,
                    self.voice,
                    rate=self.rate,
                    volume=self.volume,
                    pitch=self.pitch,
                )
                await communicate.save(output_file)
                self.log(f"[{output_file}] Conversion successful")
                return

            except Exception as e:
                last_exception = e
                self.log(f"[{output_file}] Attempt {attempt + 1} failed: {str(e)}")

            # 如果失败了,等待后重试
            if attempt < self.max_retries - 1:  # 如果不是最后一次尝试
                wait_time = 2**attempt
                self.log(f"[{output_file}] Waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

        self.log(f"[{output_file}] All attempts failed")
        raise last_exception

    async def convert_epub(self, epub_path: str) -> ConversionResult:
        """转换电子书文件为 MP3"""
        if not os.path.exists(epub_path):
            raise FileNotFoundError(f"Ebook file not found: {epub_path}")

        parsed_book = parse_book(
            epub_path,
            calibre_converter=self.ebook_convert_path,
        )
        self.book_title = parsed_book.metadata.title
        self.book_author = parsed_book.metadata.author
        self.actual_output_dir = build_book_output_dir(
            self.output_dir,
            parsed_book.metadata.title,
        )
        ensure_output_dir(self.actual_output_dir)
        chapters = parsed_book.chapters
        if self.selected_chapter_indexes is not None:
            selected_indexes = set(self.selected_chapter_indexes)
            chapters = [chapter for chapter in chapters if chapter.index in selected_indexes]
        tasks = []
        failed_chapters = []
        m4b_chapters: dict[int, M4BChapter] = {}
        completed_count = 0
        skipped_count = 0
        canceled_count = 0
        m4b_path = None
        semaphore = asyncio.Semaphore(self.max_concurrency)
        self.log(f"书名: {parsed_book.metadata.title}")
        self.log(f"作者: {parsed_book.metadata.author}")
        self.log(f"实际输出目录: {os.path.abspath(self.actual_output_dir)}")
        self.log(f"识别章节数: {len(chapters)}")

        async def run_chapter(
            index: int,
            title: str,
            content: str,
            output_path: str,
        ) -> None:
            nonlocal canceled_count, completed_count
            async with semaphore:
                if self.pause_waiter is not None:
                    await self.pause_waiter()
                if self._is_cancel_requested():
                    canceled_count += 1
                    self.log(f"Chapter {index} canceled before start.")
                    self._emit_chapter_status(index, title, CHAPTER_STATUS_CANCELED)
                    self._emit_progress(
                        total=len(chapters),
                        completed=completed_count,
                        failed=len(failed_chapters),
                        skipped=skipped_count,
                        canceled=canceled_count,
                    )
                    return
                failed_count_before = len(failed_chapters)
                self._emit_chapter_status(index, title, CHAPTER_STATUS_RUNNING)
                await self.process_chapter(
                    index,
                    title,
                    content,
                    output_path,
                    failed_chapters,
                )
                if len(failed_chapters) == failed_count_before:
                    completed_count += 1
                    m4b_chapters[index] = M4BChapter(output_path, title)
                    self._emit_chapter_status(index, title, CHAPTER_STATUS_COMPLETED)
                else:
                    self._emit_chapter_status(index, title, CHAPTER_STATUS_FAILED)
                self._emit_progress(
                    total=len(chapters),
                    completed=completed_count,
                    failed=len(failed_chapters),
                    skipped=skipped_count,
                    canceled=canceled_count,
                )

        for chapter in chapters:
            i = chapter.index
            title = chapter.title
            content = chapter.text
            safe_title = sanitize_filename(title) or f"Chapter_{i}"
            filename = f"{i:03d}_{safe_title}.mp3"
            output_path = os.path.join(self.actual_output_dir, filename)

            self.log(f"Processing chapter {i}: {title}")

            # 如果文件已存在且大小正常，跳过处理
            if (
                not self.overwrite_existing
                and os.path.exists(output_path)
                and os.path.getsize(output_path) > 0
            ):
                self.log(f"Chapter {i} already exists, skipping...")
                skipped_count += 1
                m4b_chapters[i] = M4BChapter(output_path, title)
                self._emit_chapter_status(i, title, CHAPTER_STATUS_SKIPPED)
                self._emit_progress(
                    total=len(chapters),
                    completed=completed_count,
                    failed=len(failed_chapters),
                    skipped=skipped_count,
                    canceled=canceled_count,
                )
                continue

            task = asyncio.create_task(run_chapter(i, title, content, output_path))
            tasks.append(task)

        await asyncio.gather(*tasks)
        was_canceled = canceled_count > 0 or self._is_cancel_requested()

        # 报告失败的章节
        if failed_chapters:
            self.log("\nThe following chapters failed to convert:")
            for chapter in failed_chapters:
                self.log(f"- Chapter {chapter}")

        if self.export_m4b and m4b_chapters and not was_canceled:
            ordered_chapters = [
                m4b_chapters[index]
                for index in sorted(m4b_chapters)
            ]
            m4b_output = os.path.join(
                self.actual_output_dir,
                f"{sanitize_filename(parsed_book.metadata.title) or 'audiobook'}.m4b",
            )
            try:
                m4b_path = build_m4b_audiobook(
                    chapters=ordered_chapters,
                    output_path=m4b_output,
                    book_title=parsed_book.metadata.title,
                    author=parsed_book.metadata.author,
                    cover_path=self.cover_path,
                    logger=self.log,
                )
            except Exception as exc:
                self.log(f"M4B 生成失败: {exc}")

        output_dir = os.path.abspath(self.actual_output_dir)
        summary_path = None
        try:
            summary_path = str(
                write_conversion_summary(
                    output_dir=output_dir,
                    source_path=parsed_book.source_path or epub_path,
                    book_title=parsed_book.metadata.title,
                    author=parsed_book.metadata.author,
                    language=parsed_book.metadata.language,
                    total=len(chapters),
                    completed=completed_count,
                    failed=len(failed_chapters),
                    skipped=skipped_count,
                    failed_chapters=failed_chapters.copy(),
                    canceled=was_canceled,
                    canceled_count=canceled_count,
                    m4b_path=m4b_path,
                    options=self._summary_options(),
                )
            )
        except Exception as exc:
            self.log(f"转换清单写入失败: {exc}")

        return ConversionResult(
            total=len(chapters),
            completed=completed_count,
            failed=len(failed_chapters),
            skipped=skipped_count,
            failed_chapters=failed_chapters.copy(),
            output_dir=output_dir,
            canceled=was_canceled,
            canceled_count=canceled_count,
            m4b_path=m4b_path,
            summary_path=summary_path,
        )

    def _emit_chapter_status(self, index: int, title: str, status: str) -> None:
        if self.chapter_status_callback is None:
            return
        self.chapter_status_callback(
            {
                "index": index,
                "title": title,
                "status": status,
            }
        )

    def _summary_options(self) -> dict[str, int | str | bool | None]:
        return {
            "voice": self.voice,
            "rate": self.rate,
            "volume": self.volume,
            "pitch": self.pitch,
            "max_retries": self.max_retries,
            "max_concurrency": self.max_concurrency,
            "enable_high_quality": self.enable_high_quality,
            "enable_lyrics": self.enable_lyrics,
            "enable_mp3_metadata": self.enable_mp3_metadata,
            "export_m4b": self.export_m4b,
            "overwrite_existing": self.overwrite_existing,
            "cover_path": self.cover_path,
            "ebook_convert_path": self.ebook_convert_path,
        }

    def _is_cancel_requested(self) -> bool:
        if self.cancel_checker is None:
            return False
        return self.cancel_checker()

    def _emit_progress(
        self,
        total: int,
        completed: int,
        failed: int,
        skipped: int,
        canceled: int = 0,
    ) -> None:
        if self.progress_callback is None:
            return
        self.progress_callback(
            {
                "total": total,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "canceled": canceled,
            }
        )

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
            with tempfile.NamedTemporaryFile(
                suffix=".mp3",
                dir=os.path.dirname(os.path.abspath(output_path)),
                delete=False,
            ) as tmp_file:
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
            if self.enable_mp3_metadata:
                write_mp3_chapter_metadata(
                    output_path,
                    book_title=self.book_title,
                    author=self.book_author,
                    chapter_title=title,
                    chapter_index=index,
                    cover_path=self.cover_path,
                    logger=self.log,
                )

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
                    self.log(
                        f"Failed to remove temporary file {temp_output}: {cleanup_error}"
                    )

