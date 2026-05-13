import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess

from bookvoice.calibre import find_ebook_convert, run_ebook_convert


class CalibreTests(unittest.TestCase):
    def test_find_ebook_convert_prefers_configured_path_over_path_lookup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            configured = Path(temp_dir) / "ebook-convert.exe"
            configured.write_text("placeholder", encoding="utf-8")

            result = find_ebook_convert(
                configured_path=str(configured),
                which=lambda executable: "C:\\tools\\ebook-convert.exe",
                candidate_paths=[],
                sidecar_base_dirs=[],
            )

        self.assertEqual(result, str(configured))

    def test_find_ebook_convert_checks_sidecar_before_path_lookup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sidecar = root / "calibre" / "ebook-convert.exe"
            sidecar.parent.mkdir()
            sidecar.write_text("placeholder", encoding="utf-8")

            result = find_ebook_convert(
                which=lambda executable: "C:\\tools\\ebook-convert.exe",
                candidate_paths=[],
                sidecar_base_dirs=[root],
            )

        self.assertEqual(result, str(sidecar))

    def test_find_ebook_convert_prefers_path_lookup(self):
        result = find_ebook_convert(
            which=lambda executable: "C:\\tools\\ebook-convert.exe",
            candidate_paths=[],
            sidecar_base_dirs=[],
        )

        self.assertEqual(result, "C:\\tools\\ebook-convert.exe")

    def test_find_ebook_convert_falls_back_to_existing_candidate_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "ebook-convert.exe"
            candidate.write_text("placeholder", encoding="utf-8")

            result = find_ebook_convert(
                which=lambda executable: None,
                candidate_paths=[candidate],
                sidecar_base_dirs=[],
            )

        self.assertEqual(result, str(candidate))

    def test_run_ebook_convert_builds_command_and_accepts_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "book.mobi"
            target = root / "book.epub"
            source.write_text("placeholder", encoding="utf-8")
            calls = []

            def runner(command):
                calls.append(command)
                target.write_text("converted", encoding="utf-8")
                return CompletedProcess(command, 0, stdout="ok", stderr="")

            run_ebook_convert(
                source,
                target,
                executable="ebook-convert-test",
                runner=runner,
            )

        self.assertEqual(calls, [["ebook-convert-test", str(source), str(target)]])

    def test_run_ebook_convert_reports_missing_calibre_actionably(self):
        with self.assertRaises(RuntimeError) as context:
            run_ebook_convert(
                "book.azw3",
                "book.epub",
                finder=lambda: None,
                runner=lambda command: CompletedProcess(command, 0),
            )

        message = str(context.exception)
        self.assertIn("未找到 Calibre ebook-convert", message)
        self.assertIn("MOBI/AZW3", message)
        self.assertIn("DRM", message)

    def test_run_ebook_convert_reports_failed_conversion_output(self):
        with self.assertRaises(RuntimeError) as context:
            run_ebook_convert(
                "book.mobi",
                "book.epub",
                executable="ebook-convert-test",
                runner=lambda command: CompletedProcess(
                    command,
                    1,
                    stdout="stdout text",
                    stderr="stderr text",
                ),
            )

        message = str(context.exception)
        self.assertIn("MOBI/AZW3 转换失败", message)
        self.assertIn("stderr text", message)
        self.assertIn("DRM", message)


if __name__ == "__main__":
    unittest.main()

