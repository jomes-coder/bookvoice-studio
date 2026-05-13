import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bookvoice.conversion_summary import (
    CONVERSION_SUMMARY_FILENAME,
    conversion_summary_path,
    write_conversion_summary,
)


class ConversionSummaryTests(unittest.TestCase):
    def test_conversion_summary_path_lives_in_book_output_directory(self):
        path = conversion_summary_path("D:\\audio\\书名")

        self.assertEqual(path, Path("D:\\audio\\书名") / CONVERSION_SUMMARY_FILENAME)

    def test_write_conversion_summary_writes_readable_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            summary_path = write_conversion_summary(
                output_dir=str(output_dir),
                source_path="D:\\books\\book.epub",
                book_title="测试书",
                author="作者",
                language="zh-CN",
                total=3,
                completed=2,
                failed=1,
                skipped=0,
                failed_chapters=[3],
                canceled=False,
                canceled_count=0,
                m4b_path="D:\\audio\\测试书\\测试书.m4b",
                options={
                    "voice": "zh-CN-XiaoxiaoNeural",
                    "rate": "+15%",
                    "volume": "+10%",
                    "pitch": "+0Hz",
                    "max_concurrency": 2,
                },
                generated_at=datetime(2026, 5, 13, 12, 30, tzinfo=timezone.utc),
            )

            data = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(summary_path.name, CONVERSION_SUMMARY_FILENAME)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["generated_at"], "2026-05-13T12:30:00+00:00")
        self.assertEqual(data["source_path"], "D:\\books\\book.epub")
        self.assertEqual(data["book"]["title"], "测试书")
        self.assertEqual(data["book"]["author"], "作者")
        self.assertEqual(data["book"]["language"], "zh-CN")
        self.assertEqual(data["result"]["total"], 3)
        self.assertEqual(data["result"]["completed"], 2)
        self.assertEqual(data["result"]["failed"], 1)
        self.assertEqual(data["result"]["failed_chapters"], [3])
        self.assertEqual(data["result"]["m4b_path"], "D:\\audio\\测试书\\测试书.m4b")
        self.assertEqual(data["options"]["voice"], "zh-CN-XiaoxiaoNeural")


if __name__ == "__main__":
    unittest.main()

