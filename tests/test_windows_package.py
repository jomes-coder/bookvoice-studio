import unittest
from pathlib import Path

from bookvoice.windows_package import (
    build_pyinstaller_args,
    pyinstaller_missing_message,
)


class WindowsPackageTests(unittest.TestCase):
    def test_build_pyinstaller_args_target_gui_entry_and_collect_runtime_assets(self):
        project_root = Path("D:/product/bookvoice")

        args = build_pyinstaller_args(project_root)

        self.assertIn("--noconsole", args)
        self.assertIn("--name=BookVoiceStudio", args)
        self.assertIn(f"--paths={project_root / 'src'}", args)
        self.assertIn("--collect-all=imageio_ffmpeg", args)
        self.assertIn("--collect-submodules=edge_tts", args)
        self.assertEqual(args[-1], str(project_root / "src" / "bookvoice" / "gui_entry.py"))

    def test_pyinstaller_missing_message_has_actionable_install_command(self):
        message = pyinstaller_missing_message()

        self.assertIn("PyInstaller", message)
        self.assertIn(".venv\\Scripts\\python.exe -m pip install pyinstaller", message)


if __name__ == "__main__":
    unittest.main()

