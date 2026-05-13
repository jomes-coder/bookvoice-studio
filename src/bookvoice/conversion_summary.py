import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONVERSION_SUMMARY_FILENAME = "conversion_summary.json"
SUMMARY_SCHEMA_VERSION = 1


def conversion_summary_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / CONVERSION_SUMMARY_FILENAME


def write_conversion_summary(
    *,
    output_dir: str | Path,
    source_path: str,
    book_title: str,
    author: str,
    language: str,
    total: int,
    completed: int,
    failed: int,
    skipped: int,
    failed_chapters: list[int],
    canceled: bool,
    canceled_count: int,
    m4b_path: str | None,
    options: dict[str, Any],
    generated_at: datetime | None = None,
) -> Path:
    path = conversion_summary_path(output_dir)
    timestamp = generated_at or datetime.now(timezone.utc).astimezone()
    payload = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "generated_at": timestamp.isoformat(timespec="seconds"),
        "source_path": source_path,
        "output_dir": str(output_dir),
        "book": {
            "title": book_title,
            "author": author,
            "language": language,
        },
        "result": {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "failed_chapters": failed_chapters,
            "canceled": canceled,
            "canceled_count": canceled_count,
            "m4b_path": m4b_path,
        },
        "options": options,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
