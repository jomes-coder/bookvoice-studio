import os
import subprocess
import sys
import unittest
from pathlib import Path


class DirectScriptTests(unittest.TestCase):
    def test_main_script_can_show_help_when_run_directly(self):
        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "src" / "bookvoice" / "main.py"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        result = subprocess.run(
            [sys.executable, str(script_path), "-h"],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--concurrency", result.stdout)


if __name__ == "__main__":
    unittest.main()

