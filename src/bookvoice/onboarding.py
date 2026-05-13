import os
from pathlib import Path

from .branding import APP_STATE_DIR_NAME, PRODUCT_NAME, PRODUCT_NAME_CN

APP_NAME = APP_STATE_DIR_NAME
STARTUP_GUIDE_TITLE = f"{PRODUCT_NAME_CN} 首次使用指南"
STARTUP_GUIDE_FLAG_FILENAME = "first_run_guide_seen"


def default_state_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if os.name == "nt" and appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / f".{APP_NAME}"


def startup_guide_flag_path(state_dir: Path | None = None) -> Path:
    base_dir = state_dir or default_state_dir()
    return base_dir / STARTUP_GUIDE_FLAG_FILENAME


def should_show_startup_guide(state_dir: Path | None = None) -> bool:
    return not startup_guide_flag_path(state_dir).exists()


def mark_startup_guide_seen(state_dir: Path | None = None) -> None:
    flag_path = startup_guide_flag_path(state_dir)
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text("seen\n", encoding="utf-8")


def build_startup_guide_message() -> str:
    return "\n".join(
        [
            "1. 先点“环境检查”，确认 Python 依赖和 ffmpeg 可用。",
            "2. 选择 EPUB/TXT/DOCX/MOBI/AZW3，右侧会预览章节；双击章节可切换是否转换。",
            "3. 选择音色、语速、输出目录，也可以按需关闭高质量转码或歌词标签。",
            "4. 点击“开始转换”；多本书可用“批量添加”和“开始队列”。",
            "5. 输出会自动保存到“输出目录/书名/”，常用设置会在下次启动时恢复。",
            "日志写入项目根目录的每日日志文件。",
            "转换中可以暂停、继续或取消；失败章节可点“重试失败”。",
            f"当前产品：{PRODUCT_NAME}（{PRODUCT_NAME_CN}）。",
            "完整说明书见 docs/user-guide.md。",
        ]
    )
