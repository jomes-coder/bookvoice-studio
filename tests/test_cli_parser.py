import unittest

from bookvoice.main import build_parser


class CliParserTests(unittest.TestCase):
    def test_parser_accepts_speed_and_post_processing_flags(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "book.epub",
                "--concurrency",
                "4",
                "--no-high-quality",
                "--no-lyrics",
                "--rate",
                "+15%",
                "--volume=+5%",
                "--pitch",
                "+2Hz",
                "--cover",
                "cover.jpg",
                "--m4b",
                "--no-mp3-metadata",
                "--overwrite-existing",
                "--ebook-convert",
                "D:\\Calibre\\ebook-convert.exe",
                "-b",
                "bg",
            ]
        )

        self.assertEqual(args.epub_path, "book.epub")
        self.assertEqual(args.concurrency, 4)
        self.assertTrue(args.no_high_quality)
        self.assertTrue(args.no_lyrics)
        self.assertEqual(args.rate, "+15%")
        self.assertEqual(args.volume, "+5%")
        self.assertEqual(args.pitch, "+2Hz")
        self.assertEqual(args.cover_path, "cover.jpg")
        self.assertTrue(args.m4b)
        self.assertTrue(args.no_mp3_metadata)
        self.assertTrue(args.overwrite_existing)
        self.assertEqual(args.ebook_convert_path, "D:\\Calibre\\ebook-convert.exe")
        self.assertEqual(args.bg_dir, "bg")

    def test_parser_accepts_environment_check_without_input_file(self):
        parser = build_parser()

        args = parser.parse_args(["--check-env"])

        self.assertTrue(args.check_env)
        self.assertIsNone(args.epub_path)

    def test_help_mentions_calibre_convertible_formats(self):
        parser = build_parser()

        self.assertIn("MOBI/AZW3", parser.description)


if __name__ == "__main__":
    unittest.main()

