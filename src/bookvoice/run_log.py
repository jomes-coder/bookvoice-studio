from datetime import datetime
from pathlib import Path

from .options import ConversionOptions


def daily_log_path(root_dir: Path, now: datetime | None = None) -> Path:
    current = now or datetime.now()
    return root_dir / f"日志{current:%Y%m%d}.txt"


class DailyLogWriter:
    def __init__(self, root_dir: Path, now: datetime | None = None):
        self.now = now or datetime.now()
        self.path = daily_log_path(root_dir, self.now)

    def append(self, message: str) -> None:
        with self.path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{message}\n")

    def write_run_header(self, options: ConversionOptions, voice_label: str) -> None:
        lines = [
            "",
            f"===== {self.now:%Y-%m-%d %H:%M:%S} 开始转换 =====",
            f"电子书: {options.epub_path}",
            f"输出目录: {options.output_dir}",
            f"音色: {voice_label}",
            f"真实音色: {options.voice}",
            f"语速: {options.rate}",
            f"音量: {options.volume}",
            f"音调: {options.pitch}",
            f"封面图片: {options.cover_path or '未设置'}",
            f"Calibre 路径: {options.ebook_convert_path or '自动检测'}",
            f"重试次数: {options.retries}",
            f"并发章节数: {options.max_concurrency}",
            f"背景音乐目录: {options.bg_dir or '未设置'}",
            f"高质量转码: {'开启' if options.enable_high_quality else '关闭'}",
            f"写入歌词标签: {'开启' if options.enable_lyrics else '关闭'}",
            f"写入 MP3 元数据: {'开启' if options.enable_mp3_metadata else '关闭'}",
            f"生成 M4B: {'开启' if options.export_m4b else '关闭'}",
            f"覆盖已有章节: {'开启' if options.overwrite_existing else '关闭'}",
            "",
        ]
        with self.path.open("a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines))
