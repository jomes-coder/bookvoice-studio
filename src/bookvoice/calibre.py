import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path


EBOOK_CONVERT_EXECUTABLE = "ebook-convert"
CALIBRE_MISSING_MESSAGE = (
    "未找到 Calibre ebook-convert。请安装 Calibre 后重试；"
    "MOBI/AZW3 为实验支持，DRM 加密文件不支持。"
)
CALIBRE_CONVERSION_HINT = "MOBI/AZW3 为实验支持，DRM 加密文件不支持。"
DEFAULT_WINDOWS_EBOOK_CONVERT_PATHS = (
    Path("C:/Program Files/Calibre2/ebook-convert.exe"),
    Path("C:/Program Files (x86)/Calibre2/ebook-convert.exe"),
)


def find_ebook_convert(
    executable: str = EBOOK_CONVERT_EXECUTABLE,
    which: Callable[[str], str | None] = shutil.which,
    candidate_paths: Sequence[str | Path] | None = None,
    configured_path: str | Path | None = None,
    sidecar_base_dirs: Sequence[str | Path] | None = None,
) -> str | None:
    if configured_path:
        path = Path(configured_path).expanduser()
        return str(path) if path.is_file() else None

    sidecar = _first_existing_path(sidecar_ebook_convert_paths(sidecar_base_dirs))
    if sidecar:
        return sidecar

    found = which(executable)
    if found:
        return found

    candidates = candidate_paths
    if candidates is None:
        candidates = DEFAULT_WINDOWS_EBOOK_CONVERT_PATHS if os.name == "nt" else ()

    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return str(path)
    return None


def sidecar_ebook_convert_paths(
    base_dirs: Sequence[str | Path] | None = None,
    executable: str = EBOOK_CONVERT_EXECUTABLE,
) -> tuple[Path, ...]:
    executable_name = _sidecar_executable_name(executable)
    roots = default_sidecar_base_dirs() if base_dirs is None else base_dirs
    return tuple(Path(root) / "calibre" / executable_name for root in roots)


def default_sidecar_base_dirs() -> tuple[Path, ...]:
    roots: list[Path] = []
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)
    roots.append(Path.cwd())
    roots.append(Path(__file__).resolve().parents[2])
    return _unique_paths(roots)


def _sidecar_executable_name(executable: str) -> str:
    if os.name == "nt" and not executable.lower().endswith(".exe"):
        return f"{executable}.exe"
    return executable


def _first_existing_path(paths: Sequence[str | Path]) -> str | None:
    for candidate in paths:
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path)
    return None


def _unique_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return tuple(unique)


def run_ebook_convert(
    source_path: str | Path,
    output_epub_path: str | Path,
    *,
    executable: str | None = None,
    finder: Callable[[], str | None] | None = None,
    runner: Callable[[list[str]], subprocess.CompletedProcess] | None = None,
) -> None:
    converter = executable
    if converter is None:
        converter = finder() if finder is not None else find_ebook_convert()
    if not converter:
        raise RuntimeError(CALIBRE_MISSING_MESSAGE)

    command = [converter, str(source_path), str(output_epub_path)]
    try:
        completed = (
            runner(command)
            if runner is not None
            else subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        )
    except FileNotFoundError as exc:
        raise RuntimeError(CALIBRE_MISSING_MESSAGE) from exc

    if completed.returncode != 0:
        detail = _completed_process_output(completed)
        raise RuntimeError(f"MOBI/AZW3 转换失败: {detail}；{CALIBRE_CONVERSION_HINT}")

    if not Path(output_epub_path).exists():
        raise RuntimeError(
            f"Calibre 转换完成但未生成 EPUB 文件: {output_epub_path}；"
            f"{CALIBRE_CONVERSION_HINT}"
        )


def _completed_process_output(completed: subprocess.CompletedProcess) -> str:
    parts = []
    stdout = getattr(completed, "stdout", "") or ""
    stderr = getattr(completed, "stderr", "") or ""
    if stderr:
        parts.append(f"stderr: {stderr}".strip())
    if stdout:
        parts.append(f"stdout: {stdout}".strip())
    if parts:
        return "；".join(parts)
    return f"退出代码 {completed.returncode}"
