from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .book import SUPPORTED_EBOOK_EXTENSIONS
from .audio_product import SUPPORTED_COVER_EXTENSIONS


DEFAULT_VOICE = "zh-CN-YunxiaNeural"
DEFAULT_OUTPUT_DIR = "output_audio"
DEFAULT_RETRIES = 3
DEFAULT_MAX_CONCURRENCY = 3
DEFAULT_RATE = "+0%"
DEFAULT_VOLUME = "+0%"
DEFAULT_PITCH = "+0Hz"


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
    rate: str = DEFAULT_RATE
    volume: str = DEFAULT_VOLUME
    pitch: str = DEFAULT_PITCH
    selected_chapter_indexes: tuple[int, ...] | None = None
    cover_path: Optional[str] = None
    enable_mp3_metadata: bool = True
    export_m4b: bool = False
    overwrite_existing: bool = False
    ebook_convert_path: Optional[str] = None


def validate_conversion_inputs(options: ConversionOptions) -> list[str]:
    errors: list[str] = []

    if not options.epub_path:
        errors.append("Ebook file path is required.")
    else:
        epub_path = Path(options.epub_path)
        if not epub_path.exists():
            errors.append(f"Ebook file does not exist: {options.epub_path}")
        elif not epub_path.is_file():
            errors.append(f"Ebook path is not a file: {options.epub_path}")
        elif epub_path.suffix.lower() not in SUPPORTED_EBOOK_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EBOOK_EXTENSIONS))
            errors.append(
                f"Unsupported ebook format: {epub_path.suffix.lower() or '(none)'}. "
                f"Supported formats: {supported}"
            )

    if not options.output_dir:
        errors.append("Output directory is required.")

    if options.retries < 1:
        errors.append("Retry count must be at least 1.")

    if options.max_concurrency < 1:
        errors.append("Concurrent chapter count must be at least 1.")

    if not options.rate.strip():
        errors.append("Speech rate is required.")

    if not options.volume.strip():
        errors.append("Speech volume is required.")

    if not options.pitch.strip():
        errors.append("Speech pitch is required.")

    if options.bg_dir:
        bg_path = Path(options.bg_dir)
        if not bg_path.exists():
            errors.append(f"Background music directory does not exist: {options.bg_dir}")
        elif not bg_path.is_dir():
            errors.append(f"Background music path is not a directory: {options.bg_dir}")

    if options.cover_path:
        cover_path = Path(options.cover_path)
        if not cover_path.exists():
            errors.append(f"Cover image does not exist: {options.cover_path}")
        elif not cover_path.is_file():
            errors.append(f"Cover image path is not a file: {options.cover_path}")
        elif cover_path.suffix.lower() not in SUPPORTED_COVER_EXTENSIONS:
            supported = ", ".join(SUPPORTED_COVER_EXTENSIONS)
            errors.append(
                f"Unsupported cover image format: {cover_path.suffix.lower() or '(none)'}. "
                f"Supported formats: {supported}"
            )

    if options.ebook_convert_path:
        ebook_convert_path = Path(options.ebook_convert_path)
        if not ebook_convert_path.exists():
            errors.append(
                f"Calibre ebook-convert path does not exist: {options.ebook_convert_path}"
            )
        elif not ebook_convert_path.is_file():
            errors.append(
                f"Calibre ebook-convert path is not a file: {options.ebook_convert_path}"
            )

    return errors
