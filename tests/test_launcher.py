import unittest
from pathlib import Path


class LauncherTests(unittest.TestCase):
    def test_windows_gui_launcher_exists_and_runs_gui_module(self):
        project_root = Path(__file__).resolve().parents[1]
        launcher = project_root / "start_gui.bat"

        self.assertTrue(launcher.exists())
        content = launcher.read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH", content)
        self.assertIn("-m bookvoice.gui", content)

    def test_windows_build_launcher_exists_and_runs_packaging_script(self):
        project_root = Path(__file__).resolve().parents[1]
        launcher = project_root / "build_windows.bat"

        self.assertTrue(launcher.exists())
        content = launcher.read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH", content)
        self.assertIn("tools\\build_windows_exe.py", content)


if __name__ == "__main__":
    unittest.main()

