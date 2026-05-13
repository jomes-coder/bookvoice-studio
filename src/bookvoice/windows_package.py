from pathlib import Path

from .branding import DIST_APP_NAME


def build_pyinstaller_args(project_root: Path) -> list[str]:
    root = project_root.resolve()
    return [
        "--noconfirm",
        "--clean",
        "--onedir",
        "--noconsole",
        f"--name={DIST_APP_NAME}",
        f"--distpath={root / 'dist'}",
        f"--workpath={root / 'build' / 'pyinstaller'}",
        f"--specpath={root / 'build'}",
        f"--paths={root / 'src'}",
        "--collect-all=imageio_ffmpeg",
        "--collect-submodules=edge_tts",
        "--collect-submodules=ebooklib",
        "--hidden-import=bs4",
        str(root / "src" / "bookvoice" / "gui_entry.py"),
    ]


def pyinstaller_missing_message() -> str:
    return (
        "未安装 PyInstaller，无法生成 Windows 可执行文件。\n"
        "请先运行：.venv\\Scripts\\python.exe -m pip install pyinstaller\n"
        "安装后再双击 build_windows.bat。"
    )
