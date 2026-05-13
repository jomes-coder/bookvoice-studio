import tempfile
import unittest
from pathlib import Path

from bookvoice.onboarding import (
    STARTUP_GUIDE_TITLE,
    build_startup_guide_message,
    default_state_dir,
    mark_startup_guide_seen,
    should_show_startup_guide,
)


class OnboardingTests(unittest.TestCase):
    def test_startup_guide_message_describes_main_gui_workflow(self):
        message = build_startup_guide_message()

        self.assertEqual(STARTUP_GUIDE_TITLE, "书声工坊 首次使用指南")
        self.assertIn("1. 先点“环境检查”", message)
        self.assertIn("2. 选择 EPUB/TXT/DOCX", message)
        self.assertIn("3. 选择音色、语速、输出目录", message)
        self.assertIn("4. 点击“开始转换”", message)
        self.assertIn("完整说明书", message)
        self.assertNotIn("TODO", message)

    def test_first_run_guide_flag_is_stored_in_state_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)

            self.assertTrue(should_show_startup_guide(state_dir))
            mark_startup_guide_seen(state_dir)

            self.assertFalse(should_show_startup_guide(state_dir))

    def test_default_state_dir_uses_bookvoice_studio_app_name(self):
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Tester\\AppData\\Roaming"}):
            path = default_state_dir()

        self.assertEqual(path.name, "BookVoiceStudio")


if __name__ == "__main__":
    unittest.main()

