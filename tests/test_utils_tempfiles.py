import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bookvoice.utils import add_bgm, convert_mp3_high_quality


class UtilsTempfileTests(unittest.TestCase):
    def test_high_quality_temp_file_is_created_next_to_input_mp3(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_mp3 = root / "input.mp3"
            input_mp3.write_bytes(b"input")
            replace_sources = []

            def fake_run(command, *args, **kwargs):
                Path(command[-1]).write_bytes(b"converted")

            def fake_replace(source, destination):
                replace_sources.append(Path(source))
                Path(destination).write_bytes(Path(source).read_bytes())
                Path(source).unlink()

            with patch("bookvoice.utils.get_ffmpeg_exe", return_value="ffmpeg"):
                with patch("bookvoice.utils.subprocess.run", side_effect=fake_run):
                    with patch("bookvoice.utils.os.replace", side_effect=fake_replace):
                        convert_mp3_high_quality(
                            str(input_mp3),
                            logger=lambda message: None,
                        )

            self.assertEqual(len(replace_sources), 1)
            self.assertEqual(replace_sources[0].parent.resolve(), root.resolve())

    def test_bgm_temp_file_is_created_next_to_main_audio(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            main_audio = root / "main.mp3"
            bgm_audio = root / "bgm.mp3"
            main_audio.write_bytes(b"main")
            bgm_audio.write_bytes(b"bgm")
            replace_sources = []

            def fake_run(command, *args, **kwargs):
                Path(command[-1]).write_bytes(b"mixed")

            def fake_replace(source, destination):
                replace_sources.append(Path(source))
                Path(destination).write_bytes(Path(source).read_bytes())
                Path(source).unlink()

            with patch("bookvoice.utils.get_ffmpeg_exe", return_value="ffmpeg"):
                with patch("bookvoice.utils.subprocess.run", side_effect=fake_run):
                    with patch("bookvoice.utils.os.replace", side_effect=fake_replace):
                        result = add_bgm(
                            str(main_audio),
                            str(bgm_audio),
                            logger=lambda message: None,
                        )

            self.assertTrue(result)
            self.assertEqual(len(replace_sources), 1)
            self.assertEqual(replace_sources[0].parent.resolve(), root.resolve())


if __name__ == "__main__":
    unittest.main()

