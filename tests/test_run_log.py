import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from bookvoice.options import ConversionOptions
from bookvoice.run_log import DailyLogWriter, daily_log_path


class RunLogTests(unittest.TestCase):
    def test_daily_log_path_uses_chinese_date_filename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = daily_log_path(Path(temp_dir), datetime(2026, 5, 13, 10, 42, 18))

        self.assertEqual(path.name, "日志20260513.txt")

    def test_writer_appends_run_header_and_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options = ConversionOptions(
                epub_path="D:\\books\\book.epub",
                output_dir="D:\\audio",
                voice="zh-CN-XiaoxiaoNeural",
                retries=3,
                max_concurrency=2,
                enable_high_quality=False,
                enable_lyrics=True,
                rate="+15%",
                volume="+5%",
                pitch="+2Hz",
                cover_path="D:\\books\\cover.jpg",
                enable_mp3_metadata=True,
                export_m4b=True,
                overwrite_existing=True,
            )
            writer = DailyLogWriter(
                Path(temp_dir),
                now=datetime(2026, 5, 13, 10, 42, 18),
            )

            writer.write_run_header(options, "晓晓 - 女声，普通话（zh-CN-XiaoxiaoNeural）")
            writer.append("转换完成！")

            content = writer.path.read_text(encoding="utf-8")

        self.assertIn("===== 2026-05-13 10:42:18 开始转换 =====", content)
        self.assertIn("电子书: D:\\books\\book.epub", content)
        self.assertIn("音色: 晓晓 - 女声，普通话（zh-CN-XiaoxiaoNeural）", content)
        self.assertIn("真实音色: zh-CN-XiaoxiaoNeural", content)
        self.assertIn("并发章节数: 2", content)
        self.assertIn("语速: +15%", content)
        self.assertIn("音量: +5%", content)
        self.assertIn("音调: +2Hz", content)
        self.assertIn("封面图片: D:\\books\\cover.jpg", content)
        self.assertIn("写入 MP3 元数据: 开启", content)
        self.assertIn("生成 M4B: 开启", content)
        self.assertIn("覆盖已有章节: 开启", content)
        self.assertIn("高质量转码: 关闭", content)
        self.assertIn("写入歌词标签: 开启", content)
        self.assertIn("转换完成！", content)


if __name__ == "__main__":
    unittest.main()

