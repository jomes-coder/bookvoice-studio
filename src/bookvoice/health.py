import importlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from imageio_ffmpeg import get_ffmpeg_exe

from .calibre import find_ebook_convert


REQUIRED_MODULES = [
    "edge_tts",
    "ebooklib",
    "bs4",
    "mutagen",
    "imageio_ffmpeg",
]


@dataclass(frozen=True)
class HealthCheck:
    name: str
    ok: bool
    message: str


def check_python_version(
    version_info: Sequence[int] = sys.version_info,
) -> HealthCheck:
    version = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"
    if tuple(version_info[:2]) >= (3, 12):
        return HealthCheck("Python", True, f"当前版本 {version}")
    return HealthCheck("Python", False, f"当前版本 {version}，需要 Python 3.12+")


def check_import(module_name: str) -> HealthCheck:
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return HealthCheck(module_name, False, f"未安装或不可用: {exc}")
    return HealthCheck(module_name, True, "可用")


def check_ffmpeg(
    ffmpeg_getter: Callable[[], str] = get_ffmpeg_exe,
) -> HealthCheck:
    try:
        ffmpeg_path = ffmpeg_getter()
    except Exception as exc:
        return HealthCheck("ffmpeg", False, f"不可用: {exc}")
    return HealthCheck("ffmpeg", True, ffmpeg_path)


def check_ebook_convert(
    locator: Callable[[], str | None] = find_ebook_convert,
) -> HealthCheck:
    try:
        converter_path = locator()
    except Exception as exc:
        return HealthCheck(
            "ebook-convert",
            False,
            f"检查失败: {exc}；仅 MOBI/AZW3 需要。",
        )
    if converter_path:
        return HealthCheck(
            "ebook-convert",
            True,
            f"{converter_path}（MOBI/AZW3 实验支持可用）",
        )
    return HealthCheck(
        "ebook-convert",
        False,
        "未找到 Calibre ebook-convert；仅 MOBI/AZW3 需要。"
        "请安装 Calibre 后重试，DRM 加密文件不支持。",
    )


def run_environment_checks(
    ebook_convert_path: str | None = None,
) -> list[HealthCheck]:
    checks = [check_python_version()]
    checks.extend(check_import(module_name) for module_name in REQUIRED_MODULES)
    checks.append(check_ffmpeg())
    if ebook_convert_path:
        checks.append(
            check_ebook_convert(
                lambda: find_ebook_convert(configured_path=ebook_convert_path)
            )
        )
    else:
        checks.append(check_ebook_convert())
    return checks


def format_health_checks(checks: list[HealthCheck]) -> str:
    lines = ["环境检查结果:"]
    for check in checks:
        status = "OK" if check.ok else "FAIL"
        lines.append(f"[{status}] {check.name}: {check.message}")
    return "\n".join(lines)
