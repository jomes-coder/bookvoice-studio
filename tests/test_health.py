import sys
import unittest
from unittest.mock import patch

from bookvoice.health import (
    HealthCheck,
    check_ebook_convert,
    check_ffmpeg,
    check_import,
    check_python_version,
    format_health_checks,
    run_environment_checks,
)


class HealthCheckTests(unittest.TestCase):
    def test_check_python_version_accepts_supported_version(self):
        result = check_python_version((3, 12, 0))

        self.assertTrue(result.ok)
        self.assertEqual(result.name, "Python")

    def test_check_python_version_rejects_old_version(self):
        result = check_python_version((3, 11, 9))

        self.assertFalse(result.ok)
        self.assertIn("需要 Python 3.12+", result.message)

    def test_check_import_reports_missing_module(self):
        result = check_import("definitely_missing_bookvoice_module")

        self.assertFalse(result.ok)
        self.assertIn("未安装", result.message)

    def test_check_ffmpeg_uses_supplied_getter(self):
        result = check_ffmpeg(lambda: "D:\\tools\\ffmpeg.exe")

        self.assertTrue(result.ok)
        self.assertIn("ffmpeg.exe", result.message)

    def test_check_ebook_convert_reports_available_converter(self):
        result = check_ebook_convert(
            lambda: "C:\\Program Files\\Calibre2\\ebook-convert.exe"
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.name, "ebook-convert")
        self.assertIn("MOBI/AZW3", result.message)

    def test_check_ebook_convert_reports_optional_missing_converter(self):
        result = check_ebook_convert(lambda: None)

        self.assertFalse(result.ok)
        self.assertEqual(result.name, "ebook-convert")
        self.assertIn("仅 MOBI/AZW3 需要", result.message)
        self.assertIn("Calibre", result.message)

    def test_format_health_checks_marks_success_and_failure(self):
        output = format_health_checks(
            [
                HealthCheck("A", True, "ok"),
                HealthCheck("B", False, "bad"),
            ]
        )

        self.assertIn("[OK] A: ok", output)
        self.assertIn("[FAIL] B: bad", output)

    def test_environment_checks_use_configured_ebook_convert_path(self):
        configured = "D:\\Calibre\\ebook-convert.exe"
        with patch(
            "bookvoice.health.check_python_version",
            return_value=HealthCheck("Python", True, "ok"),
        ):
            with patch(
                "bookvoice.health.check_import",
                return_value=HealthCheck("module", True, "ok"),
            ):
                with patch(
                    "bookvoice.health.check_ffmpeg",
                    return_value=HealthCheck("ffmpeg", True, "ok"),
                ):
                    with patch(
                        "bookvoice.health.find_ebook_convert",
                        return_value=configured,
                    ) as locator:
                        checks = run_environment_checks(
                            ebook_convert_path=configured,
                        )

        locator.assert_called_once_with(configured_path=configured)
        self.assertEqual(checks[-1].name, "ebook-convert")
        self.assertTrue(checks[-1].ok)


if __name__ == "__main__":
    unittest.main()

