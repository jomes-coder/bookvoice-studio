import unittest
from pathlib import Path


class UserGuideTests(unittest.TestCase):
    def test_user_guide_exists_and_covers_main_workflows(self):
        project_root = Path(__file__).resolve().parents[1]
        guide = project_root / "docs" / "user-guide.md"

        self.assertTrue(guide.exists())
        content = guide.read_text(encoding="utf-8")

        required_sections = [
            "# BookVoice Studio 使用说明书",
            "## 1. 快速开始",
            "## 2. 单本电子书转换",
            "## 3. 批量队列",
            "## 4. 参数说明",
            "## 5. 输出文件说明",
            "## 6. 日志和排错",
            "## 7. Windows 打包",
            "## 8. 常见问题",
        ]
        for section in required_sections:
            self.assertIn(section, content)

        self.assertIn("EPUB/TXT/DOCX", content)
        self.assertIn("M4B", content)
        self.assertIn("元数据", content)
        self.assertNotIn("TODO", content)

    def test_readme_links_to_user_guide(self):
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("[使用说明书](docs/user-guide.md)", readme)

    def test_acceptance_checklist_exists_for_v1_release(self):
        project_root = Path(__file__).resolve().parents[1]
        checklist = project_root / "docs" / "release" / "v1_acceptance_checklist.md"

        self.assertTrue(checklist.exists())
        content = checklist.read_text(encoding="utf-8")

        for expected in [
            "EPUB",
            "TXT",
            "DOCX",
            "MOBI",
            "AZW3",
            "Windows 打包",
            "M4B",
            "任务恢复",
        ]:
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()

