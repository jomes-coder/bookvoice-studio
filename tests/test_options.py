import tempfile
import unittest
from pathlib import Path

from bookvoice.options import ConversionOptions, validate_conversion_inputs


class ConversionOptionsTests(unittest.TestCase):
    def test_valid_inputs_have_no_errors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            epub_path = root / "book.epub"
            epub_path.write_text("placeholder", encoding="utf-8")
            output_dir = root / "out"
            bg_dir = root / "bg"
            bg_dir.mkdir()

            options = ConversionOptions(
                epub_path=str(epub_path),
                output_dir=str(output_dir),
                voice="zh-CN-YunxiaNeural",
                retries=3,
                bg_dir=str(bg_dir),
                max_concurrency=3,
                enable_high_quality=True,
                enable_lyrics=True,
            )

            self.assertEqual(validate_conversion_inputs(options), [])

    def test_accepts_txt_input(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as txt_file:
            options = ConversionOptions(
                epub_path=txt_file.name,
                output_dir="output_audio",
            )

            errors = validate_conversion_inputs(options)

        self.assertEqual(errors, [])

    def test_accepts_mobi_and_azw3_inputs(self):
        for suffix in (".mobi", ".azw3"):
            with self.subTest(suffix=suffix):
                with tempfile.NamedTemporaryFile(suffix=suffix) as ebook_file:
                    options = ConversionOptions(
                        epub_path=ebook_file.name,
                        output_dir="output_audio",
                    )

                    errors = validate_conversion_inputs(options)

                self.assertEqual(errors, [])

    def test_rejects_unsupported_ebook_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
            options = ConversionOptions(
                epub_path=pdf_file.name,
                output_dir="output_audio",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn(
            "Unsupported ebook format: .pdf. Supported formats: .azw3, .docx, .epub, .mobi, .txt",
            errors,
        )

    def test_defaults_include_speech_parameters(self):
        options = ConversionOptions(epub_path="book.epub", output_dir="output_audio")

        self.assertEqual(options.rate, "+0%")
        self.assertEqual(options.volume, "+0%")
        self.assertEqual(options.pitch, "+0Hz")
        self.assertIsNone(options.cover_path)
        self.assertTrue(options.enable_mp3_metadata)
        self.assertFalse(options.export_m4b)
        self.assertFalse(options.overwrite_existing)
        self.assertIsNone(options.ebook_convert_path)

    def test_rejects_empty_speech_parameters(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                rate="",
                volume=" ",
                pitch="",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Speech rate is required.", errors)
        self.assertIn("Speech volume is required.", errors)
        self.assertIn("Speech pitch is required.", errors)

    def test_rejects_missing_epub_path(self):
        options = ConversionOptions(epub_path="", output_dir="output_audio")

        errors = validate_conversion_inputs(options)

        self.assertIn("Ebook file path is required.", errors)

    def test_rejects_nonexistent_epub_path(self):
        options = ConversionOptions(
            epub_path="missing.epub",
            output_dir="output_audio",
        )

        errors = validate_conversion_inputs(options)

        self.assertIn("Ebook file does not exist: missing.epub", errors)

    def test_rejects_epub_path_that_is_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options = ConversionOptions(
                epub_path=temp_dir,
                output_dir="output_audio",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn(f"Ebook path is not a file: {temp_dir}", errors)

    def test_rejects_empty_output_dir(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Output directory is required.", errors)

    def test_rejects_invalid_retry_count(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                retries=0,
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Retry count must be at least 1.", errors)

    def test_rejects_invalid_concurrency(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                max_concurrency=0,
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Concurrent chapter count must be at least 1.", errors)

    def test_rejects_invalid_background_music_directory(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                bg_dir="missing-bg",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Background music directory does not exist: missing-bg", errors)

    def test_rejects_invalid_ebook_convert_path(self):
        with tempfile.NamedTemporaryFile(suffix=".mobi") as ebook_file:
            options = ConversionOptions(
                epub_path=ebook_file.name,
                output_dir="output_audio",
                ebook_convert_path="missing-ebook-convert.exe",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Calibre ebook-convert path does not exist: missing-ebook-convert.exe", errors)

    def test_rejects_missing_cover_image(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            options = ConversionOptions(
                epub_path=epub_file.name,
                output_dir="output_audio",
                cover_path="missing-cover.jpg",
            )

            errors = validate_conversion_inputs(options)

        self.assertIn("Cover image does not exist: missing-cover.jpg", errors)

    def test_rejects_unsupported_cover_image_format(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as epub_file:
            with tempfile.NamedTemporaryFile(suffix=".gif") as cover_file:
                options = ConversionOptions(
                    epub_path=epub_file.name,
                    output_dir="output_audio",
                    cover_path=cover_file.name,
                )

                errors = validate_conversion_inputs(options)

        self.assertIn("Unsupported cover image format: .gif. Supported formats: .jpg, .jpeg, .png", errors)


if __name__ == "__main__":
    unittest.main()

