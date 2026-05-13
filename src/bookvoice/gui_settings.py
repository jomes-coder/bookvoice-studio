import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .onboarding import default_state_dir
from .options import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_RETRIES,
    DEFAULT_VOLUME,
    DEFAULT_VOICE,
    ConversionOptions,
)


GUI_SETTINGS_FILENAME = "gui_settings.json"


@dataclass(frozen=True)
class GuiSettings:
    voice: str = DEFAULT_VOICE
    output_dir: str = DEFAULT_OUTPUT_DIR
    bg_dir: str = ""
    cover_path: str = ""
    retries: int = DEFAULT_RETRIES
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    rate: str = DEFAULT_RATE
    volume: str = DEFAULT_VOLUME
    pitch: str = DEFAULT_PITCH
    enable_high_quality: bool = True
    enable_lyrics: bool = True
    enable_mp3_metadata: bool = True
    export_m4b: bool = False
    overwrite_existing: bool = False
    ebook_convert_path: str = ""


def default_gui_settings() -> GuiSettings:
    return GuiSettings()


def gui_settings_path(state_dir: Path | None = None) -> Path:
    return (state_dir or default_state_dir()) / GUI_SETTINGS_FILENAME


def load_gui_settings(state_dir: Path | None = None) -> GuiSettings:
    path = gui_settings_path(state_dir)
    if not path.exists():
        return default_gui_settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return default_gui_settings()
    if not isinstance(data, dict):
        return default_gui_settings()
    return _settings_from_dict(data)


def save_gui_settings(settings: GuiSettings, state_dir: Path | None = None) -> None:
    path = gui_settings_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def settings_from_options(options: ConversionOptions) -> GuiSettings:
    return GuiSettings(
        voice=options.voice,
        output_dir=options.output_dir,
        bg_dir=options.bg_dir or "",
        cover_path=options.cover_path or "",
        retries=options.retries,
        max_concurrency=options.max_concurrency,
        rate=options.rate,
        volume=options.volume,
        pitch=options.pitch,
        enable_high_quality=options.enable_high_quality,
        enable_lyrics=options.enable_lyrics,
        enable_mp3_metadata=options.enable_mp3_metadata,
        export_m4b=options.export_m4b,
        overwrite_existing=options.overwrite_existing,
        ebook_convert_path=options.ebook_convert_path or "",
    )


def _settings_from_dict(data: dict[str, Any]) -> GuiSettings:
    defaults = default_gui_settings()
    return GuiSettings(
        voice=_str_value(data.get("voice"), defaults.voice),
        output_dir=_str_value(data.get("output_dir"), defaults.output_dir),
        bg_dir=_str_value(data.get("bg_dir"), defaults.bg_dir),
        cover_path=_str_value(data.get("cover_path"), defaults.cover_path),
        retries=_int_value(data.get("retries"), defaults.retries),
        max_concurrency=_int_value(
            data.get("max_concurrency"),
            defaults.max_concurrency,
        ),
        rate=_str_value(data.get("rate"), defaults.rate),
        volume=_str_value(data.get("volume"), defaults.volume),
        pitch=_str_value(data.get("pitch"), defaults.pitch),
        enable_high_quality=_bool_value(
            data.get("enable_high_quality"),
            defaults.enable_high_quality,
        ),
        enable_lyrics=_bool_value(data.get("enable_lyrics"), defaults.enable_lyrics),
        enable_mp3_metadata=_bool_value(
            data.get("enable_mp3_metadata"),
            defaults.enable_mp3_metadata,
        ),
        export_m4b=_bool_value(data.get("export_m4b"), defaults.export_m4b),
        overwrite_existing=_bool_value(
            data.get("overwrite_existing"),
            defaults.overwrite_existing,
        ),
        ebook_convert_path=_str_value(
            data.get("ebook_convert_path"),
            defaults.ebook_convert_path,
        ),
    )


def _str_value(value: Any, default: str) -> str:
    return value if isinstance(value, str) else default


def _int_value(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int) and value > 0:
        return value
    return default


def _bool_value(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default
