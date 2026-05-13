import tempfile
import unittest
from pathlib import Path

from bookvoice.gui_settings import (
    GUI_SETTINGS_FILENAME,
    GuiSettings,
    default_gui_settings,
    gui_settings_path,
    load_gui_settings,
    save_gui_settings,
    settings_from_options,
)
from bookvoice.options import ConversionOptions


class GuiSettingsTests(unittest.TestCase):
    def test_default_settings_match_conversion_defaults(self):
        settings = default_gui_settings()

        self.assertEqual(settings.voice, "zh-CN-YunxiaNeural")
        self.assertEqual(settings.output_dir, "output_audio")
        self.assertEqual(settings.retries, 3)
        self.assertEqual(settings.max_concurrency, 3)
        self.assertEqual(settings.rate, "+0%")
        self.assertEqual(settings.volume, "+0%")
        self.assertEqual(settings.pitch, "+0Hz")
        self.assertTrue(settings.enable_high_quality)
        self.assertTrue(settings.enable_lyrics)
        self.assertTrue(settings.enable_mp3_metadata)
        self.assertFalse(settings.export_m4b)
        self.assertFalse(settings.overwrite_existing)
        self.assertEqual(settings.ebook_convert_path, "")

    def test_settings_path_uses_state_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = gui_settings_path(Path(temp_dir))

        self.assertEqual(path.name, GUI_SETTINGS_FILENAME)
        self.assertEqual(path.parent, Path(temp_dir))

    def test_save_and_load_settings_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            settings = GuiSettings(
                voice="zh-CN-XiaoxiaoNeural",
                output_dir="D:\\audio",
                bg_dir="D:\\bg",
                cover_path="D:\\cover.jpg",
                retries=5,
                max_concurrency=2,
                rate="+15%",
                volume="+10%",
                pitch="+10Hz",
                enable_high_quality=False,
                enable_lyrics=False,
                enable_mp3_metadata=False,
                export_m4b=True,
                overwrite_existing=True,
                ebook_convert_path="D:\\Calibre\\ebook-convert.exe",
            )

            save_gui_settings(settings, state_dir)
            loaded = load_gui_settings(state_dir)

        self.assertEqual(loaded, settings)

    def test_load_settings_ignores_missing_or_corrupt_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            self.assertEqual(load_gui_settings(state_dir), default_gui_settings())

            gui_settings_path(state_dir).write_text("{bad json", encoding="utf-8")

            self.assertEqual(load_gui_settings(state_dir), default_gui_settings())

    def test_settings_from_options_omits_current_ebook_path_and_selection(self):
        options = ConversionOptions(
            epub_path="D:\\books\\book.epub",
            output_dir="D:\\audio",
            voice="zh-CN-XiaoxiaoNeural",
            retries=4,
            bg_dir="D:\\bg",
            max_concurrency=2,
            enable_high_quality=False,
            enable_lyrics=False,
            rate="+15%",
            volume="+10%",
            pitch="+10Hz",
            selected_chapter_indexes=(1, 2),
            cover_path="D:\\cover.jpg",
            enable_mp3_metadata=False,
            export_m4b=True,
            overwrite_existing=True,
            ebook_convert_path="D:\\Calibre\\ebook-convert.exe",
        )

        settings = settings_from_options(options)

        self.assertFalse(hasattr(settings, "epub_path"))
        self.assertFalse(hasattr(settings, "selected_chapter_indexes"))
        self.assertEqual(settings.output_dir, "D:\\audio")
        self.assertEqual(settings.voice, "zh-CN-XiaoxiaoNeural")
        self.assertEqual(settings.ebook_convert_path, "D:\\Calibre\\ebook-convert.exe")


if __name__ == "__main__":
    unittest.main()

