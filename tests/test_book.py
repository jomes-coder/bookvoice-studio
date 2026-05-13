import tempfile
import unittest
import zipfile
from pathlib import Path
from subprocess import CompletedProcess

from ebooklib import epub

from bookvoice.book import (
    BookMetadata,
    ParsedBook,
    ParsedChapter,
    build_book_output_dir,
    parse_book,
    parse_calibre_convertible_book,
    parse_epub_book,
    parse_txt_book,
    sanitize_book_folder_name,
)


class BookModelTests(unittest.TestCase):
    def test_sanitize_book_folder_name_removes_windows_invalid_characters(self):
        name = sanitize_book_folder_name('  测试<书>:"/\\|?*  ')

        self.assertEqual(name, "测试书")

    def test_sanitize_book_folder_name_falls_back_when_blank(self):
        name = sanitize_book_folder_name(' <>:"/\\|?* ')

        self.assertEqual(name, "未命名书籍")

    def test_build_book_output_dir_uses_sanitized_title(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = build_book_output_dir(temp_dir, ' 测试<书> ')

        self.assertEqual(output_dir, str(Path(temp_dir) / "测试书"))

    def test_parsed_book_exports_legacy_chapter_tuples(self):
        parsed = ParsedBook(
            metadata=BookMetadata(title="书名", author="作者"),
            chapters=[
                ParsedChapter(index=1, title="第一章", text="内容一", source_id="a.xhtml"),
                ParsedChapter(index=2, title="第二章", text="内容二", source_id="b.xhtml"),
            ],
        )

        self.assertEqual(
            parsed.chapters_as_tuples(),
            [("第一章", "内容一"), ("第二章", "内容二")],
        )


class EpubParsingTests(unittest.TestCase):
    def test_parse_epub_book_reads_metadata_spine_order_and_toc_titles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "source-name.epub"
            self._write_sample_epub(epub_path)

            parsed = parse_epub_book(str(epub_path))

        self.assertEqual(parsed.metadata.title, "测试书名")
        self.assertEqual(parsed.metadata.author, "作者名")
        self.assertEqual(parsed.metadata.language, "zh-CN")
        self.assertEqual([chapter.title for chapter in parsed.chapters], ["目录第一章", "目录第二章"])
        self.assertEqual([chapter.index for chapter in parsed.chapters], [1, 2])
        self.assertIn("第一章正文", parsed.chapters[0].text)
        self.assertIn("第二章正文", parsed.chapters[1].text)

    def test_parse_epub_book_falls_back_to_file_name_when_title_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "fallback-book.epub"
            self._write_sample_epub(epub_path, title=None, author=None)

            parsed = parse_epub_book(str(epub_path))

        self.assertEqual(parsed.metadata.title, "fallback-book")
        self.assertEqual(parsed.metadata.author, "未知作者")

    def _write_sample_epub(
        self,
        epub_path: Path,
        title: str | None = "测试书名",
        author: str | None = "作者名",
    ) -> None:
        book = epub.EpubBook()
        book.set_identifier("sample-id")
        book.set_language("zh-CN")
        if title is not None:
            book.set_title(title)
        if author is not None:
            book.add_author(author)

        chapter_one = epub.EpubHtml(
            title="正文第一章",
            file_name="chap1.xhtml",
            lang="zh-CN",
        )
        chapter_one.content = (
            "<html><body><h1>正文第一章</h1><p>第一章正文。</p></body></html>"
        )

        empty = epub.EpubHtml(title="空页", file_name="empty.xhtml", lang="zh-CN")
        empty.content = "<html><body>   </body></html>"

        chapter_two = epub.EpubHtml(
            title="正文第二章",
            file_name="chap2.xhtml",
            lang="zh-CN",
        )
        chapter_two.content = (
            "<html><body><h1>正文第二章</h1><p>第二章正文。</p></body></html>"
        )

        book.add_item(chapter_one)
        book.add_item(empty)
        book.add_item(chapter_two)
        book.add_item(epub.EpubNcx())
        book.toc = (
            epub.Link("chap1.xhtml", "目录第一章", "chap1"),
            epub.Link("chap2.xhtml", "目录第二章", "chap2"),
        )
        book.spine = [chapter_one, empty, chapter_two]

        epub.write_epub(str(epub_path), book)


class TxtParsingTests(unittest.TestCase):
    def test_parse_txt_book_splits_common_chapter_headings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            txt_path = Path(temp_dir) / "测试小说.txt"
            txt_path.write_text(
                "序言内容\n"
                "第一章 开始\n"
                "第一章正文。\n"
                "第二章 继续\n"
                "第二章正文。\n",
                encoding="utf-8",
            )

            parsed = parse_txt_book(str(txt_path))

        self.assertEqual(parsed.metadata.title, "测试小说")
        self.assertEqual([chapter.title for chapter in parsed.chapters], ["序章", "第一章 开始", "第二章 继续"])
        self.assertIn("序言内容", parsed.chapters[0].text)
        self.assertIn("第一章正文", parsed.chapters[1].text)
        self.assertIn("第二章正文", parsed.chapters[2].text)

    def test_parse_txt_book_reads_gbk_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            txt_path = Path(temp_dir) / "gbk-book.txt"
            txt_path.write_bytes("第一章 标题\n正文内容。".encode("gbk"))

            parsed = parse_txt_book(str(txt_path))

        self.assertEqual(parsed.metadata.title, "gbk-book")
        self.assertEqual(parsed.chapters[0].title, "第一章 标题")
        self.assertIn("正文内容", parsed.chapters[0].text)

    def test_parse_book_dispatches_epub_and_txt_and_rejects_unknown_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            txt_path = Path(temp_dir) / "book.txt"
            txt_path.write_text("正文内容", encoding="utf-8")
            unknown_path = Path(temp_dir) / "book.pdf"
            unknown_path.write_text("placeholder", encoding="utf-8")

            parsed = parse_book(str(txt_path))

            with self.assertRaises(ValueError) as context:
                parse_book(str(unknown_path))

        self.assertEqual(parsed.metadata.title, "book")
        self.assertIn("Unsupported ebook format", str(context.exception))


class CalibreConvertibleParsingTests(unittest.TestCase):
    def test_parse_book_dispatches_mobi_and_azw3_through_calibre_conversion(self):
        for suffix in (".mobi", ".azw3"):
            with self.subTest(suffix=suffix):
                with tempfile.TemporaryDirectory() as temp_dir:
                    source = Path(temp_dir) / f"book{suffix}"
                    source.write_text("placeholder", encoding="utf-8")
                    commands = []

                    def runner(command):
                        commands.append(command)
                        Path(command[-1]).write_text("converted", encoding="utf-8")
                        return CompletedProcess(command, 0, stdout="", stderr="")

                    def epub_parser(epub_path: str) -> ParsedBook:
                        self.assertTrue(epub_path.endswith(".epub"))
                        return ParsedBook(
                            metadata=BookMetadata(title="转换后书名", author="作者"),
                            chapters=[
                                ParsedChapter(
                                    index=1,
                                    title="第一章",
                                    text="正文",
                                    source_id="chapter.xhtml",
                                )
                            ],
                            source_path=epub_path,
                        )

                    parsed = parse_book(
                        str(source),
                        calibre_converter="ebook-convert-test",
                        calibre_runner=runner,
                        epub_parser=epub_parser,
                    )

                self.assertEqual(parsed.metadata.title, "转换后书名")
                self.assertEqual(parsed.source_path, str(source))
                self.assertEqual(commands[0][0], "ebook-convert-test")
                self.assertEqual(commands[0][1], str(source))

    def test_parse_calibre_convertible_book_removes_temporary_epub_after_parsing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "book.mobi"
            source.write_text("placeholder", encoding="utf-8")
            captured_epub_path = None

            def runner(command):
                Path(command[-1]).write_text("converted", encoding="utf-8")
                return CompletedProcess(command, 0, stdout="", stderr="")

            def epub_parser(epub_path: str) -> ParsedBook:
                nonlocal captured_epub_path
                captured_epub_path = Path(epub_path)
                self.assertTrue(captured_epub_path.exists())
                return ParsedBook(
                    metadata=BookMetadata(title="转换后书名", author="作者"),
                    chapters=[
                        ParsedChapter(
                            index=1,
                            title="第一章",
                            text="正文",
                            source_id="chapter.xhtml",
                        )
                    ],
                    source_path=epub_path,
                )

            parsed = parse_calibre_convertible_book(
                str(source),
                converter_path="ebook-convert-test",
                runner=runner,
                epub_parser=epub_parser,
            )

        self.assertEqual(parsed.source_path, str(source))
        self.assertIsNotNone(captured_epub_path)
        self.assertFalse(captured_epub_path.exists())


class DocxParsingTests(unittest.TestCase):
    def test_parse_book_reads_docx_metadata_and_heading_chapters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            docx_path = Path(temp_dir) / "sample.docx"
            self._write_sample_docx(docx_path)

            parsed = parse_book(str(docx_path))

        self.assertEqual(parsed.metadata.title, "DOCX 书名")
        self.assertEqual(parsed.metadata.author, "DOCX 作者")
        self.assertEqual([chapter.title for chapter in parsed.chapters], ["第一章 开始", "第二章 继续"])
        self.assertIn("第一章正文", parsed.chapters[0].text)
        self.assertIn("第二章正文", parsed.chapters[1].text)

    def _write_sample_docx(self, docx_path: Path) -> None:
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>第一章 开始</w:t></w:r>
    </w:p>
    <w:p><w:r><w:t>第一章正文。</w:t></w:r></w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>第二章 继续</w:t></w:r>
    </w:p>
    <w:p><w:r><w:t>第二章正文。</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
        core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
  xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>DOCX 书名</dc:title>
  <dc:creator>DOCX 作者</dc:creator>
</cp:coreProperties>
"""
        with zipfile.ZipFile(docx_path, "w") as archive:
            archive.writestr("word/document.xml", document_xml)
            archive.writestr("docProps/core.xml", core_xml)


if __name__ == "__main__":
    unittest.main()

