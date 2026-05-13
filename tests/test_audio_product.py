import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bookvoice.audio_product import (
    M4BChapter,
    build_m4b_audiobook,
    cover_mime_type,
    write_mp3_chapter_metadata,
)


class FakeID3Tags:
    def __init__(self):
        self.frames = []
        self.deleted = []
        self.saved = False

    def delall(self, frame_id):
        self.deleted.append(frame_id)

    def add(self, frame):
        self.frames.append(frame)

    def save(self, mp3_path):
        self.saved = mp3_path


class AudioProductTests(unittest.TestCase):
    def test_cover_mime_type_detects_common_image_formats(self):
        self.assertEqual(cover_mime_type("cover.jpg"), "image/jpeg")
        self.assertEqual(cover_mime_type("cover.jpeg"), "image/jpeg")
        self.assertEqual(cover_mime_type("cover.png"), "image/png")

    def test_write_mp3_chapter_metadata_writes_title_album_artist_track_and_cover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mp3_path = root / "chapter.mp3"
            cover_path = root / "cover.jpg"
            mp3_path.write_bytes(b"mp3")
            cover_path.write_bytes(b"cover")
            tags = FakeID3Tags()

            with patch("bookvoice.audio_product.ID3", return_value=tags):
                write_mp3_chapter_metadata(
                    str(mp3_path),
                    book_title="测试书",
                    author="作者",
                    chapter_title="第一章",
                    chapter_index=1,
                    cover_path=str(cover_path),
                    logger=lambda message: None,
                )

        frame_ids = [frame.FrameID for frame in tags.frames]
        self.assertIn("TIT2", frame_ids)
        self.assertIn("TALB", frame_ids)
        self.assertIn("TPE1", frame_ids)
        self.assertIn("TRCK", frame_ids)
        self.assertIn("APIC", frame_ids)
        self.assertEqual(tags.saved, str(mp3_path))

    def test_build_m4b_audiobook_uses_concat_and_chapter_metadata_in_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            chapter_1 = root / "001.mp3"
            chapter_2 = root / "002.mp3"
            chapter_1.write_bytes(b"mp3")
            chapter_2.write_bytes(b"mp3")
            output_path = root / "book.m4b"
            captured = {}

            def fake_run(command, *args, **kwargs):
                captured["command"] = command
                concat_path = Path(command[command.index("-i") + 1])
                metadata_path = Path(command[command.index("-i", command.index("-i") + 1) + 1])
                captured["concat_path"] = concat_path
                captured["metadata_path"] = metadata_path
                captured["concat_text"] = concat_path.read_text(encoding="utf-8")
                captured["metadata_text"] = metadata_path.read_text(encoding="utf-8")
                Path(command[-1]).write_bytes(b"m4b")

            durations = iter([12.5, 20.0])

            class FakeMP3:
                def __init__(self, _path):
                    self.info = type("Info", (), {"length": next(durations)})()

            with patch("bookvoice.audio_product.get_ffmpeg_exe", return_value="ffmpeg"):
                with patch("bookvoice.audio_product.MP3", FakeMP3):
                    with patch("bookvoice.audio_product.subprocess.run", side_effect=fake_run):
                        result = build_m4b_audiobook(
                            chapters=[
                                M4BChapter(str(chapter_1), "第一章"),
                                M4BChapter(str(chapter_2), "第二章"),
                            ],
                            output_path=str(output_path),
                            book_title="测试书",
                            author="作者",
                            logger=lambda message: None,
                        )

            self.assertEqual(result, str(output_path))
            self.assertTrue(output_path.exists())
            self.assertEqual(captured["concat_path"].parent.resolve(), root.resolve())
            self.assertEqual(captured["metadata_path"].parent.resolve(), root.resolve())
            self.assertIn("-f", captured["command"])
            self.assertIn("concat", captured["command"])
            self.assertIn("-map_metadata", captured["command"])
            self.assertIn("file '", captured["concat_text"])
            self.assertIn("[CHAPTER]", captured["metadata_text"])
            self.assertIn("title=第一章", captured["metadata_text"])
            self.assertIn("START=0", captured["metadata_text"])
            self.assertIn("END=12500", captured["metadata_text"])

