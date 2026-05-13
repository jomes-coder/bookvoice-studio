import asyncio
import os
import sys
import threading
import webbrowser
from dataclasses import dataclass, replace
from pathlib import Path


def _configure_tcl_paths() -> None:
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    tcl_library = os.path.join(base_prefix, "tcl", "tcl8.6")
    tk_library = os.path.join(base_prefix, "tcl", "tk8.6")

    if os.path.exists(os.path.join(tcl_library, "init.tcl")):
        os.environ.setdefault("TCL_LIBRARY", tcl_library)
    if os.path.exists(os.path.join(tk_library, "tk.tcl")):
        os.environ.setdefault("TK_LIBRARY", tk_library)


_configure_tcl_paths()

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .book import parse_book
from .branding import HEADER_TITLE, PRODUCT_NAME, WINDOW_TITLE
from .chapter_selection import ChapterSelection
from .health import format_health_checks, run_environment_checks
from .gui_settings import (
    GuiSettings,
    load_gui_settings,
    save_gui_settings,
    settings_from_options,
)
from .converter import (
    CHAPTER_STATUS_CANCELED,
    CHAPTER_STATUS_COMPLETED,
    CHAPTER_STATUS_FAILED,
    CHAPTER_STATUS_RUNNING,
    CHAPTER_STATUS_SKIPPED,
    EpubToMP3Converter,
)
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
from .onboarding import (
    STARTUP_GUIDE_TITLE,
    build_startup_guide_message,
    mark_startup_guide_seen,
    should_show_startup_guide,
)
from .run_log import DailyLogWriter
from .task_queue import CANCELED, COMPLETED, FAILED, PENDING, RUNNING, TaskQueue
from .voices import (
    COMMON_VOICES,
    fetch_edge_tts_voice_names,
    format_voice_label,
    format_voice_labels,
    verify_voice_can_speak,
    voice_id_from_label,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_LAYOUT_ROWS = {
    "section": 0,
    "epub": 1,
    "calibre": 2,
    "voice": 3,
    "speech": 4,
    "output": 5,
    "background": 6,
    "cover": 7,
    "product": 9,
    "numeric": 11,
    "progress": 13,
    "start": 14,
}
FILE_ROW_COLUMNS = {
    "label": 0,
    "entry": 1,
    "browse": 3,
    "clear": 4,
}
CALIBRE_ROW_COLUMNS = {
    "label": 0,
    "entry": 1,
    "browse": 3,
    "download": 4,
    "clear": 5,
}
FILE_ENTRY_WIDTH = 26
CALIBRE_DOWNLOAD_URL = "https://www.calibre-ebook.com/download_windows64"
BASE_BUTTON_PADDING = (6, 3)
SECONDARY_BUTTON_PADDING = (8, 4)
ACCENT_BUTTON_PADDING = (9, 5)
CONTROL_BUTTON_GAP = 6
CONTROL_BUTTON_COLUMNS = {
    "start": 0,
    "pause": 1,
    "cancel": 2,
    "retry": 3,
    "open_output": 4,
    "check_env": 5,
    "guide": 6,
}
CONTROL_BUTTON_TEXTS = {
    "start": "开始转换",
    "pause": "暂停",
    "cancel": "取消",
    "retry": "重试失败",
    "open_output": "打开目录",
    "check_env": "环境检查",
    "guide": "使用说明",
}
CONTROL_BUTTON_LAYOUT = {
    "start": (0, 0),
    "pause": (0, 1),
    "cancel": (0, 2),
    "retry": (1, 0),
    "open_output": (1, 1),
    "check_env": (1, 2),
    "guide": (1, 3),
}
PRODUCT_OPTION_LAYOUT = {
    "mp3_metadata": (0, 0),
    "m4b": (0, 1),
    "overwrite": (0, 2),
    "high_quality": (1, 0),
    "lyrics": (1, 1),
}
QUEUE_BUTTON_COLUMNS = {
    "add": 0,
    "start": 1,
    "clear": 2,
}
QUEUE_BUTTON_TEXTS = {
    "add": "批量添加",
    "start": "开始队列",
    "clear": "清空队列",
}
WORKSPACE_TABS = ("chapters", "queue", "logs")
WORKSPACE_TAB_LABELS = {
    "chapters": "章节预览",
    "queue": "批量队列",
    "logs": "转换日志",
}
QUEUE_STATUS_LABELS = {
    PENDING: "待转换",
    RUNNING: "转换中",
    COMPLETED: "已完成",
    FAILED: "失败",
    CANCELED: "已取消",
}
CHAPTER_STATUS_PENDING = "pending"
CHAPTER_STATUS_LABELS = {
    CHAPTER_STATUS_PENDING: "待转换",
    CHAPTER_STATUS_RUNNING: "转换中",
    CHAPTER_STATUS_COMPLETED: "已完成",
    CHAPTER_STATUS_FAILED: "失败",
    CHAPTER_STATUS_SKIPPED: "已跳过",
    CHAPTER_STATUS_CANCELED: "已取消",
}
CHAPTER_TREE_COLUMNS = ("selected", "index", "status", "title", "word_count")
CHAPTER_TITLE_DISPLAY_LIMIT = 42
CHAPTER_TREE_COLUMN_WIDTHS = {
    "selected": 56,
    "index": 56,
    "status": 76,
    "title": 444,
    "word_count": 96,
    "status_stretch": False,
    "word_count_stretch": False,
}
QUEUE_TREE_COLUMNS = ("index", "status", "name", "path")
EBOOK_FILE_TYPES = [
    ("电子书文件", "*.epub *.txt *.docx *.mobi *.azw3"),
    ("EPUB files", "*.epub"),
    ("Text files", "*.txt"),
    ("Word documents", "*.docx"),
    ("Kindle files", "*.mobi *.azw3"),
    ("All files", "*.*"),
]
COVER_FILE_TYPES = [
    ("图片文件", "*.jpg *.jpeg *.png"),
    ("JPEG files", "*.jpg *.jpeg"),
    ("PNG files", "*.png"),
    ("All files", "*.*"),
]
EBOOK_CONVERT_FILE_TYPES = [
    ("Calibre ebook-convert", "ebook-convert.exe"),
    ("Executable files", "*.exe"),
    ("All files", "*.*"),
]
SPEECH_RATE_OPTIONS = ["-20%", "+0%", "+15%", "+30%"]
SPEECH_VOLUME_OPTIONS = ["-20%", "+0%", "+10%", "+20%"]
SPEECH_PITCH_OPTIONS = ["-10Hz", "+0Hz", "+10Hz"]


def format_chapter_title_for_preview(title: str) -> str:
    cleaned = " ".join(title.split())
    if len(cleaned) <= CHAPTER_TITLE_DISPLAY_LIMIT:
        return cleaned
    return cleaned[: CHAPTER_TITLE_DISPLAY_LIMIT - 3].rstrip() + "..."


def chapter_status_label(status: str) -> str:
    return CHAPTER_STATUS_LABELS.get(status, status)


def chapter_row_values(
    chapter,
    selected: bool = True,
    status: str = CHAPTER_STATUS_PENDING,
) -> tuple[str, int, str, str, int]:
    return (
        "是" if selected else "否",
        chapter.index,
        chapter_status_label(status),
        format_chapter_title_for_preview(chapter.title),
        chapter.word_count,
    )


def format_queue_summary(queue: TaskQueue) -> str:
    counts = queue.status_counts()
    return (
        f"队列：共 {len(queue.items)} 本，"
        f"待转换 {counts[PENDING]}，"
        f"转换中 {counts[RUNNING]}，"
        f"已完成 {counts[COMPLETED]}，"
        f"失败 {counts[FAILED]}，"
        f"已取消 {counts[CANCELED]}"
    )


def queue_display_rows(queue: TaskQueue) -> list[tuple[int, str, str, str]]:
    rows = []
    for index, item in enumerate(queue.items, start=1):
        rows.append(
            (
                index,
                QUEUE_STATUS_LABELS.get(item.status, item.status),
                Path(item.path).name,
                item.path,
            )
        )
    return rows


def open_calibre_download_page(open_url=webbrowser.open) -> bool:
    return bool(open_url(CALIBRE_DOWNLOAD_URL))


@dataclass(frozen=True)
class PauseChange:
    button_text: str
    log_message: str


class PauseController:
    pause_text = "暂停"
    resume_text = "继续"

    def __init__(self) -> None:
        self.event = threading.Event()
        self.is_paused = False
        self.event.set()

    def reset(self) -> None:
        self.is_paused = False
        self.event.set()

    def pause(self) -> PauseChange:
        self.is_paused = True
        self.event.clear()
        return PauseChange(
            button_text=self.resume_text,
            log_message="已暂停：当前正在转换的章节会完成，后续章节等待。",
        )

    def resume(self) -> PauseChange:
        self.is_paused = False
        self.event.set()
        return PauseChange(
            button_text=self.pause_text,
            log_message="继续转换。",
        )

    def toggle(self) -> PauseChange:
        if self.is_paused:
            return self.resume()
        return self.pause()

    async def wait_while_paused(self, sleep_interval: float = 0.2) -> None:
        while not self.event.is_set():
            await asyncio.sleep(sleep_interval)


class CancelController:
    def __init__(self) -> None:
        self.event = threading.Event()

    def reset(self) -> None:
        self.event.clear()

    def request_cancel(self) -> None:
        self.event.set()

    def is_cancel_requested(self) -> bool:
        return self.event.is_set()


class BookVoiceStudioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("1180x760")
        self.root.minsize(1040, 680)
        self.is_running = False
        self.log_writer: DailyLogWriter | None = None
        self.pause_controller = PauseController()
        self.cancel_controller = CancelController()
        self.last_output_dir: str | None = None
        self.last_options: ConversionOptions | None = None
        self.last_voice_label = ""
        self.last_failed_count = 0
        self.chapter_selection = ChapterSelection()
        self.preview_chapters = []
        self.task_queue = TaskQueue()
        self.saved_settings = load_gui_settings()

        self.epub_path_var = tk.StringVar()
        self.ebook_convert_path_var = tk.StringVar(
            value=self.saved_settings.ebook_convert_path
        )
        self.voice_var = tk.StringVar(value=format_voice_label(self.saved_settings.voice))
        self.output_dir_var = tk.StringVar(value=self.saved_settings.output_dir)
        self.bg_dir_var = tk.StringVar(value=self.saved_settings.bg_dir)
        self.cover_path_var = tk.StringVar(value=self.saved_settings.cover_path)
        self.retries_var = tk.StringVar(value=str(self.saved_settings.retries))
        self.concurrency_var = tk.StringVar(value=str(self.saved_settings.max_concurrency))
        self.rate_var = tk.StringVar(value=self.saved_settings.rate)
        self.volume_var = tk.StringVar(value=self.saved_settings.volume)
        self.pitch_var = tk.StringVar(value=self.saved_settings.pitch)
        self.enable_high_quality_var = tk.BooleanVar(
            value=self.saved_settings.enable_high_quality
        )
        self.enable_lyrics_var = tk.BooleanVar(value=self.saved_settings.enable_lyrics)
        self.enable_mp3_metadata_var = tk.BooleanVar(
            value=self.saved_settings.enable_mp3_metadata
        )
        self.export_m4b_var = tk.BooleanVar(value=self.saved_settings.export_m4b)
        self.overwrite_existing_var = tk.BooleanVar(
            value=self.saved_settings.overwrite_existing
        )
        self.progress_var = tk.StringVar(value="进度：未开始")
        self.queue_status_var = tk.StringVar(value=format_queue_summary(self.task_queue))

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.root.after(700, self.show_startup_guide_if_needed)

    def _build_ui(self) -> None:
        self._configure_style()
        self.root.configure(bg="#f4f1eb")
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(18, 16, 18, 10), style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=HEADER_TITLE, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text=f"{PRODUCT_NAME}：选择电子书、音色和输出目录后开始制作有声书。",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        settings = ttk.Frame(self.root, padding=18, style="Panel.TFrame")
        settings.grid(row=1, column=0, sticky="ns", padx=(18, 10), pady=(0, 18))
        settings.columnconfigure(0, weight=0)
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(2, weight=1)
        settings.columnconfigure(3, weight=0)
        settings.columnconfigure(4, weight=0)
        settings.columnconfigure(5, weight=0)

        log_frame = ttk.Frame(self.root, padding=18, style="Panel.TFrame")
        log_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 18), pady=(0, 18))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        ttk.Label(settings, text="转换设置", style="Section.TLabel").grid(
            row=SETTINGS_LAYOUT_ROWS["section"],
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 12),
        )

        self._add_file_row(
            settings,
            SETTINGS_LAYOUT_ROWS["epub"],
            "电子书文件",
            self.epub_path_var,
            self.browse_epub,
        )
        self._add_calibre_row(
            settings,
            SETTINGS_LAYOUT_ROWS["calibre"],
            "Calibre路径",
            self.ebook_convert_path_var,
        )

        voice_row = SETTINGS_LAYOUT_ROWS["voice"]
        ttk.Label(settings, text="音色").grid(
            row=voice_row, column=0, sticky="w", pady=(8, 4)
        )
        self.voice_combo = ttk.Combobox(
            settings,
            textvariable=self.voice_var,
            values=format_voice_labels(COMMON_VOICES),
            state="readonly",
            width=FILE_ENTRY_WIDTH,
        )
        self.voice_combo.grid(row=voice_row, column=1, columnspan=2, sticky="ew")
        ttk.Button(settings, text="刷新音色", command=self.refresh_voices).grid(
            row=voice_row, column=3, padx=(CONTROL_BUTTON_GAP, 0), sticky="ew"
        )

        speech_row = SETTINGS_LAYOUT_ROWS["speech"]
        ttk.Label(settings, text="语音参数").grid(
            row=speech_row, column=0, sticky="w", pady=(8, 4)
        )
        speech_frame = ttk.Frame(settings, style="Panel.TFrame")
        speech_frame.grid(row=speech_row, column=1, columnspan=4, sticky="ew")
        for column in (1, 3, 5):
            speech_frame.columnconfigure(column, weight=1)
        ttk.Label(speech_frame, text="语速").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            speech_frame,
            textvariable=self.rate_var,
            values=SPEECH_RATE_OPTIONS,
            width=8,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 8))
        ttk.Label(speech_frame, text="音量").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            speech_frame,
            textvariable=self.volume_var,
            values=SPEECH_VOLUME_OPTIONS,
            width=8,
        ).grid(row=0, column=3, sticky="ew", padx=(4, 8))
        ttk.Label(speech_frame, text="音调").grid(row=0, column=4, sticky="w")
        ttk.Combobox(
            speech_frame,
            textvariable=self.pitch_var,
            values=SPEECH_PITCH_OPTIONS,
            width=8,
        ).grid(row=0, column=5, sticky="ew", padx=(4, 0))

        self._add_file_row(
            settings,
            SETTINGS_LAYOUT_ROWS["output"],
            "输出目录",
            self.output_dir_var,
            self.browse_output_dir,
        )
        self._add_file_row(
            settings,
            SETTINGS_LAYOUT_ROWS["background"],
            "背景音乐目录",
            self.bg_dir_var,
            self.browse_bg_dir,
            allow_clear=True,
        )
        self._add_file_row(
            settings,
            SETTINGS_LAYOUT_ROWS["cover"],
            "封面图片",
            self.cover_path_var,
            self.browse_cover,
            allow_clear=True,
        )

        product_row = SETTINGS_LAYOUT_ROWS["product"]
        product_frame = ttk.Frame(settings, style="Panel.TFrame")
        product_frame.grid(
            row=product_row,
            column=0,
            columnspan=5,
            sticky="ew",
            pady=(12, 0),
        )
        product_frame.columnconfigure(0, weight=1)
        product_frame.columnconfigure(1, weight=1)
        product_frame.columnconfigure(2, weight=1)
        ttk.Checkbutton(
            product_frame,
            text="写入 MP3 元数据",
            variable=self.enable_mp3_metadata_var,
        ).grid(
            row=PRODUCT_OPTION_LAYOUT["mp3_metadata"][0],
            column=PRODUCT_OPTION_LAYOUT["mp3_metadata"][1],
            sticky="w",
        )
        ttk.Checkbutton(
            product_frame,
            text="生成 M4B",
            variable=self.export_m4b_var,
        ).grid(
            row=PRODUCT_OPTION_LAYOUT["m4b"][0],
            column=PRODUCT_OPTION_LAYOUT["m4b"][1],
            sticky="w",
        )
        ttk.Checkbutton(
            product_frame,
            text="覆盖重转",
            variable=self.overwrite_existing_var,
        ).grid(
            row=PRODUCT_OPTION_LAYOUT["overwrite"][0],
            column=PRODUCT_OPTION_LAYOUT["overwrite"][1],
            sticky="w",
        )
        ttk.Checkbutton(
            product_frame,
            text="高质量转码",
            variable=self.enable_high_quality_var,
        ).grid(
            row=PRODUCT_OPTION_LAYOUT["high_quality"][0],
            column=PRODUCT_OPTION_LAYOUT["high_quality"][1],
            sticky="w",
            pady=(8, 0),
        )
        ttk.Checkbutton(
            product_frame,
            text="写入歌词标签",
            variable=self.enable_lyrics_var,
        ).grid(
            row=PRODUCT_OPTION_LAYOUT["lyrics"][0],
            column=PRODUCT_OPTION_LAYOUT["lyrics"][1],
            sticky="w",
            pady=(8, 0),
        )

        numeric_row = SETTINGS_LAYOUT_ROWS["numeric"]
        ttk.Label(settings, text="重试次数").grid(
            row=numeric_row, column=0, sticky="w", pady=(10, 4)
        )
        ttk.Spinbox(settings, from_=1, to=20, textvariable=self.retries_var, width=8).grid(
            row=numeric_row, column=1, sticky="w", padx=(0, 10)
        )

        ttk.Label(settings, text="并发章节数").grid(
            row=numeric_row, column=2, sticky="w", pady=(10, 4)
        )
        ttk.Spinbox(
            settings,
            from_=1,
            to=10,
            textvariable=self.concurrency_var,
            width=8,
        ).grid(row=numeric_row, column=3, sticky="w")

        ttk.Label(
            settings,
            textvariable=self.progress_var,
            style="MutedPanel.TLabel",
        ).grid(
            row=SETTINGS_LAYOUT_ROWS["progress"],
            column=0,
            columnspan=5,
            sticky="w",
            pady=(12, 0),
        )

        control_frame = ttk.Frame(settings, style="Panel.TFrame")
        control_frame.grid(
            row=SETTINGS_LAYOUT_ROWS["start"],
            column=0,
            columnspan=5,
            sticky="ew",
            pady=(18, 0),
        )
        for column in range(4):
            control_frame.columnconfigure(column, weight=1)
        self.start_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["start"],
            command=self.start_conversion,
            style="Accent.TButton",
        )
        self.start_button.grid(
            row=CONTROL_BUTTON_LAYOUT["start"][0],
            column=CONTROL_BUTTON_LAYOUT["start"][1],
            sticky="ew",
        )

        self.pause_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["pause"],
            command=self.toggle_pause,
            state="disabled",
            style="Secondary.TButton",
        )
        self.pause_button.grid(
            row=CONTROL_BUTTON_LAYOUT["pause"][0],
            column=CONTROL_BUTTON_LAYOUT["pause"][1],
            padx=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        self.cancel_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["cancel"],
            command=self.cancel_conversion,
            state="disabled",
            style="Secondary.TButton",
        )
        self.cancel_button.grid(
            row=CONTROL_BUTTON_LAYOUT["cancel"][0],
            column=CONTROL_BUTTON_LAYOUT["cancel"][1],
            padx=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        self.retry_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["retry"],
            command=self.retry_failed,
            state="disabled",
            style="Secondary.TButton",
        )
        self.retry_button.grid(
            row=CONTROL_BUTTON_LAYOUT["retry"][0],
            column=CONTROL_BUTTON_LAYOUT["retry"][1],
            pady=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        self.open_output_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["open_output"],
            command=self.open_output_dir,
            state="disabled",
            style="Secondary.TButton",
        )
        self.open_output_button.grid(
            row=CONTROL_BUTTON_LAYOUT["open_output"][0],
            column=CONTROL_BUTTON_LAYOUT["open_output"][1],
            padx=(CONTROL_BUTTON_GAP, 0),
            pady=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        self.check_env_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["check_env"],
            command=self.check_environment,
            style="Secondary.TButton",
        )
        self.check_env_button.grid(
            row=CONTROL_BUTTON_LAYOUT["check_env"][0],
            column=CONTROL_BUTTON_LAYOUT["check_env"][1],
            padx=(CONTROL_BUTTON_GAP, 0),
            pady=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        self.guide_button = ttk.Button(
            control_frame,
            text=CONTROL_BUTTON_TEXTS["guide"],
            command=self.show_startup_guide,
            style="Secondary.TButton",
        )
        self.guide_button.grid(
            row=CONTROL_BUTTON_LAYOUT["guide"][0],
            column=CONTROL_BUTTON_LAYOUT["guide"][1],
            padx=(CONTROL_BUTTON_GAP, 0),
            pady=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        workspace = ttk.Notebook(log_frame, style="Workspace.TNotebook")
        workspace.grid(row=0, column=0, sticky="nsew")
        workspace_tabs = {}
        for tab_name in WORKSPACE_TABS:
            tab = ttk.Frame(workspace, padding=14, style="Panel.TFrame")
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(1, weight=1)
            workspace.add(tab, text=WORKSPACE_TAB_LABELS[tab_name])
            workspace_tabs[tab_name] = tab

        chapters_tab = workspace_tabs["chapters"]
        queue_tab = workspace_tabs["queue"]
        logs_tab = workspace_tabs["logs"]

        ttk.Label(chapters_tab, text="章节预览", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.chapter_tree = ttk.Treeview(
            chapters_tab,
            columns=CHAPTER_TREE_COLUMNS,
            show="headings",
            height=8,
        )
        self.chapter_tree.heading("selected", text="转换")
        self.chapter_tree.heading("index", text="序号")
        self.chapter_tree.heading("status", text="状态")
        self.chapter_tree.heading("title", text="章节")
        self.chapter_tree.heading("word_count", text="字数")
        self.chapter_tree.column(
            "selected",
            width=CHAPTER_TREE_COLUMN_WIDTHS["selected"],
            anchor="center",
            stretch=False,
        )
        self.chapter_tree.column(
            "index",
            width=CHAPTER_TREE_COLUMN_WIDTHS["index"],
            anchor="center",
            stretch=False,
        )
        self.chapter_tree.column(
            "status",
            width=CHAPTER_TREE_COLUMN_WIDTHS["status"],
            anchor="center",
            stretch=CHAPTER_TREE_COLUMN_WIDTHS["status_stretch"],
        )
        self.chapter_tree.column(
            "title",
            width=CHAPTER_TREE_COLUMN_WIDTHS["title"],
            anchor="w",
        )
        self.chapter_tree.column(
            "word_count",
            width=CHAPTER_TREE_COLUMN_WIDTHS["word_count"],
            anchor="e",
            stretch=CHAPTER_TREE_COLUMN_WIDTHS["word_count_stretch"],
        )
        self.chapter_tree.grid(row=1, column=0, sticky="nsew")
        self.chapter_tree.bind("<Double-1>", self.toggle_chapter_selection)

        queue_header = ttk.Frame(queue_tab, style="Panel.TFrame")
        queue_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        queue_header.columnconfigure(0, weight=1)
        ttk.Label(queue_header, text="批量队列", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        queue_controls = ttk.Frame(queue_header, style="Panel.TFrame")
        queue_controls.grid(row=0, column=1, sticky="e")
        queue_controls.columnconfigure(QUEUE_BUTTON_COLUMNS["add"], weight=0)
        queue_controls.columnconfigure(QUEUE_BUTTON_COLUMNS["start"], weight=0)
        queue_controls.columnconfigure(QUEUE_BUTTON_COLUMNS["clear"], weight=0)
        self.add_queue_button = ttk.Button(
            queue_controls,
            text=QUEUE_BUTTON_TEXTS["add"],
            command=self.add_to_queue,
            style="Secondary.TButton",
        )
        self.add_queue_button.grid(
            row=0,
            column=QUEUE_BUTTON_COLUMNS["add"],
            sticky="ew",
        )
        self.start_queue_button = ttk.Button(
            queue_controls,
            text=QUEUE_BUTTON_TEXTS["start"],
            command=self.start_queue,
            style="Secondary.TButton",
        )
        self.start_queue_button.grid(
            row=0,
            column=QUEUE_BUTTON_COLUMNS["start"],
            padx=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )
        self.clear_queue_button = ttk.Button(
            queue_controls,
            text=QUEUE_BUTTON_TEXTS["clear"],
            command=self.clear_queue,
            style="Secondary.TButton",
        )
        self.clear_queue_button.grid(
            row=0,
            column=QUEUE_BUTTON_COLUMNS["clear"],
            padx=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

        ttk.Label(
            queue_tab,
            textvariable=self.queue_status_var,
            style="MutedPanel.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.queue_tree = ttk.Treeview(
            queue_tab,
            columns=QUEUE_TREE_COLUMNS,
            show="headings",
            height=5,
        )
        self.queue_tree.heading("index", text="序号")
        self.queue_tree.heading("status", text="状态")
        self.queue_tree.heading("name", text="文件")
        self.queue_tree.heading("path", text="路径")
        self.queue_tree.column("index", width=52, anchor="center", stretch=False)
        self.queue_tree.column("status", width=74, anchor="center", stretch=False)
        self.queue_tree.column("name", width=170, anchor="w")
        self.queue_tree.column("path", width=320, anchor="w")
        self.queue_tree.grid(row=2, column=0, sticky="nsew")
        queue_tab.rowconfigure(1, weight=0)
        queue_tab.rowconfigure(2, weight=1)

        ttk.Label(logs_tab, text="转换日志", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.log_text = tk.Text(
            logs_tab,
            wrap="word",
            state="disabled",
            bg="#171717",
            fg="#e7e1d7",
            insertbackground="#e7e1d7",
            relief="flat",
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(logs_tab, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _configure_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#f4f1eb")
        style.configure("Panel.TFrame", background="#fffdf8", relief="flat")
        style.configure("Workspace.TNotebook", background="#fffdf8", borderwidth=0)
        style.configure(
            "Workspace.TNotebook.Tab",
            padding=(16, 8),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.configure(
            "Title.TLabel",
            background="#f4f1eb",
            foreground="#2f2b25",
            font=("Microsoft YaHei UI", 18, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background="#f4f1eb",
            foreground="#756f66",
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background="#fffdf8",
            foreground="#2f2b25",
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        style.configure("TLabel", background="#fffdf8", foreground="#3d382f")
        style.configure(
            "MutedPanel.TLabel",
            background="#fffdf8",
            foreground="#756f66",
            font=("Microsoft YaHei UI", 9),
        )
        style.configure("TCheckbutton", background="#fffdf8", foreground="#3d382f")
        style.configure("TButton", padding=BASE_BUTTON_PADDING)
        style.configure(
            "Secondary.TButton",
            background="#e7dfd1",
            foreground="#2f2b25",
            padding=SECONDARY_BUTTON_PADDING,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#d9cebd"), ("disabled", "#eee8de")],
            foreground=[("disabled", "#9b9387")],
        )
        style.configure(
            "Accent.TButton",
            background="#2f6f73",
            foreground="#ffffff",
            padding=ACCENT_BUTTON_PADDING,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#245b5f"), ("disabled", "#8da7a9")],
            foreground=[("disabled", "#f4f1eb")],
        )

    def _add_file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_command,
        allow_clear: bool = False,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row,
            column=FILE_ROW_COLUMNS["label"],
            sticky="w",
            pady=(8, 4),
        )
        ttk.Entry(parent, textvariable=variable, width=FILE_ENTRY_WIDTH).grid(
            row=row,
            column=FILE_ROW_COLUMNS["entry"],
            columnspan=2,
            sticky="ew",
            padx=(0, 8),
        )
        ttk.Button(parent, text="浏览", command=browse_command).grid(
            row=row,
            column=FILE_ROW_COLUMNS["browse"],
            sticky="ew",
        )
        if allow_clear:
            ttk.Button(parent, text="清空", command=lambda: variable.set("")).grid(
                row=row,
                column=FILE_ROW_COLUMNS["clear"],
                padx=(CONTROL_BUTTON_GAP, 0),
                sticky="ew",
            )

    def _add_calibre_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row,
            column=CALIBRE_ROW_COLUMNS["label"],
            sticky="w",
            pady=(8, 4),
        )
        ttk.Entry(parent, textvariable=variable, width=FILE_ENTRY_WIDTH).grid(
            row=row,
            column=CALIBRE_ROW_COLUMNS["entry"],
            columnspan=2,
            sticky="ew",
            padx=(0, 8),
        )
        ttk.Button(parent, text="浏览", command=self.browse_ebook_convert).grid(
            row=row,
            column=CALIBRE_ROW_COLUMNS["browse"],
            sticky="ew",
        )
        ttk.Button(parent, text="下载", command=self.open_calibre_download).grid(
            row=row,
            column=CALIBRE_ROW_COLUMNS["download"],
            padx=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )
        ttk.Button(parent, text="清空", command=lambda: variable.set("")).grid(
            row=row,
            column=CALIBRE_ROW_COLUMNS["clear"],
            padx=(CONTROL_BUTTON_GAP, 0),
            sticky="ew",
        )

    def browse_epub(self) -> None:
        path = filedialog.askopenfilename(
            title="选择电子书文件",
            filetypes=EBOOK_FILE_TYPES,
        )
        if path:
            self.epub_path_var.set(path)
            self.load_chapter_preview(path)

    def browse_output_dir(self) -> None:
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)

    def browse_bg_dir(self) -> None:
        path = filedialog.askdirectory(title="选择背景音乐目录")
        if path:
            self.bg_dir_var.set(path)

    def browse_cover(self) -> None:
        path = filedialog.askopenfilename(
            title="选择封面图片",
            filetypes=COVER_FILE_TYPES,
        )
        if path:
            self.cover_path_var.set(path)

    def browse_ebook_convert(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 Calibre ebook-convert.exe",
            filetypes=EBOOK_CONVERT_FILE_TYPES,
        )
        if path:
            self.ebook_convert_path_var.set(path)

    def open_calibre_download(self) -> None:
        opened = open_calibre_download_page()
        self.append_log(f"Calibre 下载页: {CALIBRE_DOWNLOAD_URL}")
        if not opened:
            self.append_log("浏览器打开失败，请复制上面的链接到浏览器。")

    def add_to_queue(self) -> None:
        if self.is_running:
            self.append_log("转换运行中，暂不能添加队列。")
            return
        paths = filedialog.askopenfilenames(
            title="批量添加电子书",
            filetypes=EBOOK_FILE_TYPES,
        )
        if not paths:
            return
        added_count = self.task_queue.add_many(list(paths))
        self.refresh_queue_view()
        if not self.epub_path_var.get().strip():
            first_path = paths[0]
            self.epub_path_var.set(first_path)
            self.load_chapter_preview(first_path)
        self.append_log(
            f"批量队列已添加 {added_count} 本，当前共 {len(self.task_queue.items)} 本。"
        )

    def clear_queue(self) -> None:
        if self.is_running:
            self.append_log("转换运行中，暂不能清空队列。")
            return
        self.task_queue.clear()
        self.refresh_queue_view()
        self.append_log("批量队列已清空。")

    def refresh_queue_view(self) -> None:
        self.queue_tree.delete(*self.queue_tree.get_children())
        for index, status, name, path in queue_display_rows(self.task_queue):
            self.queue_tree.insert("", "end", iid=path, values=(index, status, name, path))
        self.queue_status_var.set(format_queue_summary(self.task_queue))

    def thread_safe_queue_view(self) -> None:
        self.root.after(0, self.refresh_queue_view)

    def _set_queue_controls_state(self, state: str) -> None:
        self.add_queue_button.configure(state=state)
        self.start_queue_button.configure(state=state)
        self.clear_queue_button.configure(state=state)

    def append_log(self, message: str) -> None:
        if self.log_writer is not None:
            self.log_writer.append(message)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def load_chapter_preview(self, path: str) -> None:
        try:
            parsed = parse_book(
                path,
                calibre_converter=self.ebook_convert_path_var.get().strip() or None,
            )
        except Exception as exc:
            self.append_log(f"章节预览失败: {exc}")
            return
        self.preview_chapters = parsed.chapters
        self.chapter_selection.load(parsed.chapters)
        self.chapter_tree.delete(*self.chapter_tree.get_children())
        for chapter in parsed.chapters:
            self.chapter_tree.insert(
                "",
                "end",
                iid=str(chapter.index),
                values=chapter_row_values(chapter),
            )
        self.append_log(
            f"已预览《{parsed.metadata.title}》，共 {len(parsed.chapters)} 个章节。"
        )

    def toggle_chapter_selection(self, _event=None) -> None:
        focused = self.chapter_tree.focus()
        if not focused:
            return
        index = int(focused)
        selected = self.chapter_selection.toggle(index)
        values = list(self.chapter_tree.item(focused, "values"))
        if values:
            values[0] = "是" if selected else "否"
            self.chapter_tree.item(focused, values=values)

    def thread_safe_log(self, message: str) -> None:
        self.root.after(0, self.append_log, message)

    def thread_safe_progress(self, progress: dict[str, int | str]) -> None:
        self.root.after(0, self.update_progress, progress)

    def thread_safe_chapter_status(self, event: dict[str, int | str]) -> None:
        self.root.after(0, self.update_chapter_status, event)

    def update_progress(self, progress: dict[str, int | str]) -> None:
        self.progress_var.set(
            "进度："
            f"完成 {progress.get('completed', 0)} / {progress.get('total', 0)}，"
            f"失败 {progress.get('failed', 0)}，"
            f"跳过 {progress.get('skipped', 0)}，"
            f"取消 {progress.get('canceled', 0)}"
        )

    def update_chapter_status(self, event: dict[str, int | str]) -> None:
        index = str(event.get("index", ""))
        if not index or not self.chapter_tree.exists(index):
            return
        values = list(self.chapter_tree.item(index, "values"))
        if len(values) < len(CHAPTER_TREE_COLUMNS):
            return
        values[2] = chapter_status_label(str(event.get("status", "")))
        self.chapter_tree.item(index, values=values)

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
            labels = format_voice_labels(voices)
            current_voice_id = voice_id_from_label(self.voice_var.get())
            self.voice_combo.configure(values=labels)
            if current_voice_id in voices:
                self.voice_var.set(format_voice_label(current_voice_id))
            elif labels:
                self.voice_var.set(labels[0])
            self.append_log(f"音色列表已刷新，共 {len(voices)} 个。")

        self.root.after(0, apply_voices)

    def start_conversion(self) -> None:
        if self.is_running:
            self.append_log("转换已经在运行中。")
            return

        selected_chapter_indexes = (
            self.chapter_selection.selected_indexes()
            if self.chapter_selection.has_chapters()
            else None
        )
        built = self._create_options_from_inputs(
            self.epub_path_var.get().strip(),
            selected_chapter_indexes=selected_chapter_indexes,
        )
        if built is None:
            return
        options, voice_label = built
        errors = validate_conversion_inputs(options)
        if errors:
            for error in errors:
                self.append_log(f"错误: {error}")
            return
        if options.selected_chapter_indexes == ():
            self.append_log("错误: 至少需要选择一个章节。")
            return

        self.save_current_settings(options)
        self._start_conversion(options, voice_label)

    def start_queue(self) -> None:
        if self.is_running:
            self.append_log("转换已经在运行中。")
            return
        pending_paths = self.task_queue.pending_paths()
        if not pending_paths:
            self.append_log("批量队列为空或没有待转换任务。")
            return

        built = self._create_options_from_inputs(
            pending_paths[0],
            selected_chapter_indexes=None,
        )
        if built is None:
            return
        base_options, voice_label = built
        self.save_current_settings(base_options)
        self._start_queue(base_options, voice_label)

    def _create_options_from_inputs(
        self,
        epub_path: str,
        selected_chapter_indexes: tuple[int, ...] | None,
    ) -> tuple[ConversionOptions, str] | None:
        try:
            retries = int(self.retries_var.get())
            concurrency = int(self.concurrency_var.get())
        except ValueError:
            self.append_log("错误: 重试次数和并发章节数必须是整数。")
            return

        voice_label = self.voice_var.get().strip()
        voice_id = voice_id_from_label(voice_label)
        options = ConversionOptions(
            epub_path=epub_path,
            output_dir=self.output_dir_var.get().strip(),
            voice=voice_id,
            retries=retries,
            bg_dir=self.bg_dir_var.get().strip() or None,
            max_concurrency=concurrency,
            enable_high_quality=self.enable_high_quality_var.get(),
            enable_lyrics=self.enable_lyrics_var.get(),
            rate=self.rate_var.get().strip(),
            volume=self.volume_var.get().strip(),
            pitch=self.pitch_var.get().strip(),
            selected_chapter_indexes=selected_chapter_indexes,
            cover_path=self.cover_path_var.get().strip() or None,
            enable_mp3_metadata=self.enable_mp3_metadata_var.get(),
            export_m4b=self.export_m4b_var.get(),
            overwrite_existing=self.overwrite_existing_var.get(),
            ebook_convert_path=self.ebook_convert_path_var.get().strip() or None,
        )
        return options, voice_label

    def current_settings(self) -> GuiSettings:
        return GuiSettings(
            voice=voice_id_from_label(self.voice_var.get().strip()),
            output_dir=self.output_dir_var.get().strip() or DEFAULT_OUTPUT_DIR,
            bg_dir=self.bg_dir_var.get().strip(),
            cover_path=self.cover_path_var.get().strip(),
            retries=self._positive_int_or_default(
                self.retries_var.get(),
                DEFAULT_RETRIES,
            ),
            max_concurrency=self._positive_int_or_default(
                self.concurrency_var.get(),
                DEFAULT_MAX_CONCURRENCY,
            ),
            rate=self.rate_var.get().strip() or DEFAULT_RATE,
            volume=self.volume_var.get().strip() or DEFAULT_VOLUME,
            pitch=self.pitch_var.get().strip() or DEFAULT_PITCH,
            enable_high_quality=self.enable_high_quality_var.get(),
            enable_lyrics=self.enable_lyrics_var.get(),
            enable_mp3_metadata=self.enable_mp3_metadata_var.get(),
            export_m4b=self.export_m4b_var.get(),
            overwrite_existing=self.overwrite_existing_var.get(),
            ebook_convert_path=self.ebook_convert_path_var.get().strip(),
        )

    def save_current_settings(self, options: ConversionOptions | None = None) -> None:
        settings = settings_from_options(options) if options is not None else self.current_settings()
        save_gui_settings(settings)

    def close_window(self) -> None:
        try:
            self.save_current_settings()
        except OSError as exc:
            self.append_log(f"设置保存失败: {exc}")
        self.root.destroy()

    def _positive_int_or_default(self, value: str, default: int) -> int:
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed > 0 else default

    def _start_conversion(
        self,
        options: ConversionOptions,
        voice_label: str,
        retrying: bool = False,
    ) -> None:
        self.log_writer = DailyLogWriter(PROJECT_ROOT)
        self.log_writer.write_run_header(options, voice_label)
        self.append_log(f"日志文件: {self.log_writer.path}")
        self.is_running = True
        self.last_options = options
        self.last_voice_label = voice_label
        self.last_failed_count = 0
        self.last_output_dir = None
        self.pause_controller.reset()
        self.cancel_controller.reset()
        self.progress_var.set("进度：准备转换")
        self.start_button.configure(state="disabled")
        self.retry_button.configure(state="disabled")
        self.open_output_button.configure(state="disabled")
        self._set_queue_controls_state("disabled")
        self.cancel_button.configure(state="normal")
        self.pause_button.configure(
            state="normal",
            text=self.pause_controller.pause_text,
        )
        self.append_log("开始重试失败章节..." if retrying else "开始转换...")
        threading.Thread(target=self._conversion_worker, args=(options,), daemon=True).start()

    def _start_queue(
        self,
        base_options: ConversionOptions,
        voice_label: str,
    ) -> None:
        self.log_writer = DailyLogWriter(PROJECT_ROOT)
        self.log_writer.write_run_header(base_options, voice_label)
        self.append_log(f"日志文件: {self.log_writer.path}")
        self.is_running = True
        self.last_options = None
        self.last_voice_label = voice_label
        self.last_failed_count = 0
        self.last_output_dir = None
        self.pause_controller.reset()
        self.cancel_controller.reset()
        self.progress_var.set("进度：准备批量转换")
        self.start_button.configure(state="disabled")
        self.retry_button.configure(state="disabled")
        self.open_output_button.configure(state="disabled")
        self._set_queue_controls_state("disabled")
        self.cancel_button.configure(state="normal")
        self.pause_button.configure(
            state="normal",
            text=self.pause_controller.pause_text,
        )
        self.append_log(f"开始批量队列，共 {len(self.task_queue.pending_paths())} 本。")
        threading.Thread(
            target=self._queue_worker,
            args=(base_options,),
            daemon=True,
        ).start()

    def retry_failed(self) -> None:
        if self.is_running:
            self.append_log("转换运行中，暂不能重试。")
            return
        if self.last_options is None or self.last_failed_count <= 0:
            self.append_log("当前没有可重试的失败章节。")
            return
        self._start_conversion(
            self.last_options,
            self.last_voice_label or self.last_options.voice,
            retrying=True,
        )

    def cancel_conversion(self) -> None:
        if not self.is_running:
            self.append_log("当前没有正在运行的转换。")
            return
        self.cancel_controller.request_cancel()
        self.cancel_button.configure(state="disabled")
        self.append_log("已请求取消：当前正在转换的章节会完成，后续章节停止。")

    def toggle_pause(self) -> None:
        if not self.is_running:
            self.append_log("当前没有正在运行的转换。")
            return

        change = self.pause_controller.toggle()
        self.pause_button.configure(text=change.button_text)
        self.append_log(change.log_message)

    def open_output_dir(self) -> None:
        if not self.last_output_dir or not os.path.isdir(self.last_output_dir):
            self.append_log("输出目录暂不可用。")
            return
        if hasattr(os, "startfile"):
            os.startfile(self.last_output_dir)
        else:
            self.append_log(f"输出目录: {self.last_output_dir}")

    def check_environment(self) -> None:
        self.append_log(
            format_health_checks(
                run_environment_checks(
                    ebook_convert_path=self.ebook_convert_path_var.get().strip() or None
                )
            )
        )

    def show_startup_guide_if_needed(self) -> None:
        try:
            if should_show_startup_guide():
                self.show_startup_guide()
        except OSError as exc:
            self.append_log(f"首次使用指南状态读取失败: {exc}")

    def show_startup_guide(self) -> None:
        messagebox.showinfo(
            STARTUP_GUIDE_TITLE,
            build_startup_guide_message(),
            parent=self.root,
        )
        try:
            mark_startup_guide_seen()
        except OSError as exc:
            self.append_log(f"首次使用指南状态保存失败: {exc}")

    def _verify_voice_or_raise(self, options: ConversionOptions) -> None:
        self.thread_safe_log(f"正在检测音色: {options.voice}")
        try:
            asyncio.run(
                verify_voice_can_speak(
                    options.voice,
                    rate=options.rate,
                    volume=options.volume,
                    pitch=options.pitch,
                )
            )
        except Exception as exc:
            raise RuntimeError(f"音色自检失败: {exc}") from exc
        self.thread_safe_log("音色自检通过。")

    def _run_converter(self, options: ConversionOptions):
        converter = EpubToMP3Converter(
            voice=options.voice,
            output_dir=options.output_dir,
            max_retries=options.retries,
            bg_dir=options.bg_dir,
            max_concurrency=options.max_concurrency,
            enable_high_quality=options.enable_high_quality,
            enable_lyrics=options.enable_lyrics,
            rate=options.rate,
            volume=options.volume,
            pitch=options.pitch,
            selected_chapter_indexes=options.selected_chapter_indexes,
            cover_path=options.cover_path,
            enable_mp3_metadata=options.enable_mp3_metadata,
            export_m4b=options.export_m4b,
            overwrite_existing=options.overwrite_existing,
            ebook_convert_path=options.ebook_convert_path,
            logger=self.thread_safe_log,
            pause_waiter=self.pause_controller.wait_while_paused,
            cancel_checker=self.cancel_controller.is_cancel_requested,
            progress_callback=self.thread_safe_progress,
            chapter_status_callback=self.thread_safe_chapter_status,
        )
        return asyncio.run(converter.convert_epub(options.epub_path))

    def _log_conversion_result(self, result) -> None:
        self.thread_safe_log("转换完成！")
        self.thread_safe_log(
            "结果: "
            f"总章节 {result.total}, "
            f"成功 {result.completed}, "
            f"跳过 {result.skipped}, "
            f"失败 {result.failed}, "
            f"取消 {result.canceled_count}"
        )
        if result.canceled:
            self.thread_safe_log("转换已取消。")
        if result.failed_chapters:
            self.thread_safe_log(f"失败章节: {result.failed_chapters}")
        if result.m4b_path:
            self.thread_safe_log(f"M4B 文件: {result.m4b_path}")
        self.thread_safe_log(f"所有音频文件已保存到目录: {result.output_dir}")

    def _conversion_worker(self, options: ConversionOptions) -> None:
        try:
            self._verify_voice_or_raise(options)
            result = self._run_converter(options)
            self.last_failed_count = result.failed
            self.last_output_dir = result.output_dir
            self._log_conversion_result(result)
            if result.failed_chapters:
                self.last_options = replace(
                    options,
                    selected_chapter_indexes=tuple(result.failed_chapters),
                )
        except Exception as exc:
            self.thread_safe_log(f"转换过程中出现错误: {exc}")
        finally:
            self.root.after(0, self._conversion_finished)

    def _queue_worker(self, base_options: ConversionOptions) -> None:
        try:
            self._verify_voice_or_raise(base_options)
            for path in list(self.task_queue.pending_paths()):
                if self.cancel_controller.is_cancel_requested():
                    self._mark_pending_queue_items_canceled()
                    break

                options = replace(
                    base_options,
                    epub_path=path,
                    selected_chapter_indexes=None,
                )
                self.task_queue.mark_running(path)
                self.thread_safe_queue_view()
                self.thread_safe_log(f"队列开始: {Path(path).name}")

                validation_errors = validate_conversion_inputs(options)
                if validation_errors:
                    for error in validation_errors:
                        self.thread_safe_log(f"队列任务错误: {error}")
                    self.task_queue.mark_failed(path)
                    self.thread_safe_queue_view()
                    continue

                try:
                    result = self._run_converter(options)
                except Exception as exc:
                    self.task_queue.mark_failed(path)
                    self.thread_safe_queue_view()
                    self.thread_safe_log(f"队列任务失败: {Path(path).name}: {exc}")
                    continue

                self.last_output_dir = result.output_dir
                self._log_conversion_result(result)
                if result.failed_chapters:
                    self.last_failed_count = result.failed
                    self.last_options = replace(
                        options,
                        selected_chapter_indexes=tuple(result.failed_chapters),
                    )

                if result.canceled:
                    self.task_queue.mark_canceled(path)
                    self._mark_pending_queue_items_canceled()
                    self.thread_safe_log(f"队列已取消: {Path(path).name}")
                    break
                if result.failed > 0:
                    self.task_queue.mark_failed(path)
                else:
                    self.task_queue.mark_completed(path)
                self.thread_safe_queue_view()
            self.thread_safe_log("批量队列处理结束。")
        except Exception as exc:
            self.thread_safe_log(f"批量队列出现错误: {exc}")
        finally:
            self.root.after(0, self._conversion_finished)

    def _mark_pending_queue_items_canceled(self) -> None:
        for path in self.task_queue.pending_paths():
            self.task_queue.mark_canceled(path)
        self.thread_safe_queue_view()

    def _conversion_finished(self) -> None:
        self.is_running = False
        self.pause_controller.reset()
        self.start_button.configure(state="normal")
        self._set_queue_controls_state("normal")
        self.pause_button.configure(
            state="disabled",
            text=self.pause_controller.pause_text,
        )
        self.cancel_button.configure(state="disabled")
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            self.open_output_button.configure(state="normal")
        else:
            self.open_output_button.configure(state="disabled")
        if self.last_failed_count > 0 and self.last_options is not None:
            self.retry_button.configure(state="normal")
        else:
            self.retry_button.configure(state="disabled")
        self.refresh_queue_view()


def main() -> None:
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    root = tk.Tk()
    BookVoiceStudioApp(root)
    root.mainloop()


Epub2Mp3App = BookVoiceStudioApp


if __name__ == "__main__":
    main()
