import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bookvoice.windows_package import (  # noqa: E402
    build_pyinstaller_args,
    pyinstaller_missing_message,
)


def main() -> int:
    try:
        import PyInstaller.__main__
    except ImportError:
        print(pyinstaller_missing_message())
        return 1

    PyInstaller.__main__.run(build_pyinstaller_args(PROJECT_ROOT))
    print("Windows 可执行文件已生成到 dist\\BookVoiceStudio。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
