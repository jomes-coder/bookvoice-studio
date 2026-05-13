import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from imageio_ffmpeg import get_ffmpeg_exe
from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TALB, TIT2, TPE1, TRCK, Encoding
from mutagen.mp3 import MP3


SUPPORTED_COVER_EXTENSIONS = (".jpg", ".jpeg", ".png")


@dataclass(frozen=True)
class M4BChapter:
    path: str
    title: str


def cover_mime_type(cover_path: str) -> str:
    suffix = Path(cover_path).suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    return "application/octet-stream"


def write_mp3_chapter_metadata(
    mp3_path: str,
    *,
    book_title: str,
    author: str,
    chapter_title: str,
    chapter_index: int,
    cover_path: str | None = None,
    logger: Callable[[str], None] = print,
) -> None:
    try:
        try:
            tags = ID3(mp3_path)
        except ID3NoHeaderError:
            tags = ID3()

        for frame_id in ("TIT2", "TALB", "TPE1", "TRCK", "APIC"):
            tags.delall(frame_id)

        tags.add(TIT2(encoding=Encoding.UTF8, text=chapter_title))
        tags.add(TALB(encoding=Encoding.UTF8, text=book_title))
        tags.add(TPE1(encoding=Encoding.UTF8, text=author))
        tags.add(TRCK(encoding=Encoding.UTF8, text=str(chapter_index)))

        if cover_path:
            cover = Path(cover_path)
            tags.add(
                APIC(
                    encoding=Encoding.UTF8,
                    mime=cover_mime_type(str(cover)),
                    type=3,
                    desc="cover",
                    data=cover.read_bytes(),
                )
            )

        tags.save(mp3_path)
        logger(f"[{mp3_path}] MP3 元数据写入成功")
    except Exception as exc:
        logger(f"[{mp3_path}] MP3 元数据写入失败: {exc}")


def build_m4b_audiobook(
    *,
    chapters: list[M4BChapter],
    output_path: str,
    book_title: str,
    author: str,
    cover_path: str | None = None,
    logger: Callable[[str], None] = print,
) -> str:
    if not chapters:
        raise ValueError("M4B chapters cannot be empty.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    concat_path = None
    metadata_path = None

    try:
        concat_path = _write_concat_file(chapters, output.parent)
        metadata_path = _write_ffmetadata_file(chapters, output.parent, book_title, author)
        command = _build_m4b_command(
            concat_path=concat_path,
            metadata_path=metadata_path,
            output_path=output,
            cover_path=Path(cover_path) if cover_path else None,
        )

        logger(f"正在生成 M4B: {output}")
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger(f"M4B 已生成: {output}")
        return str(output)
    finally:
        for temp_path in (concat_path, metadata_path):
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass


def _build_m4b_command(
    *,
    concat_path: Path,
    metadata_path: Path,
    output_path: Path,
    cover_path: Path | None,
) -> list[str]:
    command = [
        get_ffmpeg_exe(),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-i",
        str(metadata_path),
    ]
    if cover_path:
        command.extend(["-i", str(cover_path), "-map", "0:a", "-map", "2:v"])
    else:
        command.extend(["-map", "0:a"])
    command.extend(
        [
            "-map_metadata",
            "1",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
        ]
    )
    if cover_path:
        command.extend(["-c:v", "copy", "-disposition:v", "attached_pic"])
    command.extend(["-movflags", "+faststart", str(output_path)])
    return command


def _write_concat_file(chapters: list[M4BChapter], output_dir: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        dir=output_dir,
        delete=False,
    ) as file:
        for chapter in chapters:
            file.write(f"file '{_concat_path(chapter.path)}'\n")
        return Path(file.name)


def _write_ffmetadata_file(
    chapters: list[M4BChapter],
    output_dir: Path,
    book_title: str,
    author: str,
) -> Path:
    start_ms = 0
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        dir=output_dir,
        delete=False,
    ) as file:
        file.write(";FFMETADATA1\n")
        file.write(f"title={_metadata_text(book_title)}\n")
        file.write(f"artist={_metadata_text(author)}\n")
        for chapter in chapters:
            duration_ms = max(1, int(MP3(chapter.path).info.length * 1000))
            end_ms = start_ms + duration_ms
            file.write("[CHAPTER]\n")
            file.write("TIMEBASE=1/1000\n")
            file.write(f"START={start_ms}\n")
            file.write(f"END={end_ms}\n")
            file.write(f"title={_metadata_text(chapter.title)}\n")
            start_ms = end_ms
        return Path(file.name)


def _concat_path(path: str) -> str:
    normalized = Path(path).resolve().as_posix()
    return normalized.replace("'", "'\\''")


def _metadata_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("=", "\\=")
        .replace(";", "\\;")
        .replace("#", "\\#")
    )
