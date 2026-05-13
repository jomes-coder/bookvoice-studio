"""Legacy compatibility package for the renamed BookVoice Studio project."""

from __future__ import annotations

import importlib
import sys


_SUBMODULES = (
    "audio_product",
    "book",
    "branding",
    "calibre",
    "chapter_selection",
    "conversion_summary",
    "converter",
    "gui_settings",
    "health",
    "onboarding",
    "options",
    "run_log",
    "task_queue",
    "utils",
    "voices",
    "windows_package",
)

for _name in _SUBMODULES:
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(f"bookvoice.{_name}")
