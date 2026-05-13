import re
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from .calibre import run_ebook_convert


INVALID_WINDOWS_NAME_CHARS = r'[<>:"/\\|?*]'
DEFAULT_BOOK_TITLE = "未命名书籍"
UNKNOWN_AUTHOR = "未知作者"
CALIBRE_CONVERTIBLE_EXTENSIONS = {".mobi", ".azw3"}
SUPPORTED_EBOOK_EXTENSIONS = {
    ".epub",
    ".txt",
    ".docx",
    *CALIBRE_CONVERTIBLE_EXTENSIONS,
}
TXT_CHAPTER_PATTERN = re.compile(
    r"^\s*((第\s*[零〇一二三四五六七八九十百千万\d]+\s*[章节卷集部篇回][^\n]*)|(Chapter\s+[\divxlcdm]+[^\n]*))\s*$",
    re.IGNORECASE,
)
TXT_SENTENCE_ENDINGS = ("。", "，", "！", "？", "；", ".", ",", "!", "?", ";")


@dataclass(frozen=True)
class BookMetadata:
    title: str
    author: str = UNKNOWN_AUTHOR
    language: str = ""
    cover: str | None = None


@dataclass(frozen=True)
class ParsedChapter:
    index: int
    title: str
    text: str
    source_id: str
    word_count: int = 0
    is_selected: bool = True
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedBook:
    metadata: BookMetadata
    chapters: list[ParsedChapter]
    source_path: str = ""

    def chapters_as_tuples(self) -> list[tuple[str, str]]:
        return [(chapter.title, chapter.text) for chapter in self.chapters]


def sanitize_book_folder_name(name: str) -> str:
    cleaned = re.sub(INVALID_WINDOWS_NAME_CHARS, "", name).strip().strip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or DEFAULT_BOOK_TITLE


def build_book_output_dir(output_root: str, book_title: str) -> str:
    return str(Path(output_root) / sanitize_book_folder_name(book_title))


def parse_epub_book(epub_path: str) -> ParsedBook:
    source = Path(epub_path)
    book = epub.read_epub(str(source), options={"ignore_ncx": True})
    metadata = _extract_metadata(book, source)
    toc_titles = _collect_toc_titles(book.toc)
    chapters = _extract_chapters(book, toc_titles)
    return ParsedBook(metadata=metadata, chapters=chapters, source_path=str(source))


def parse_book(
    book_path: str,
    *,
    calibre_converter: str | None = None,
    calibre_runner: Callable[[list[str]], object] | None = None,
    epub_parser: Callable[[str], ParsedBook] = parse_epub_book,
) -> ParsedBook:
    source = Path(book_path)
    extension = source.suffix.lower()
    if extension == ".epub":
        return epub_parser(book_path)
    if extension == ".txt":
        return parse_txt_book(book_path)
    if extension == ".docx":
        return parse_docx_book(book_path)
    if extension in CALIBRE_CONVERTIBLE_EXTENSIONS:
        return parse_calibre_convertible_book(
            book_path,
            converter_path=calibre_converter,
            runner=calibre_runner,
            epub_parser=epub_parser,
        )
    supported = ", ".join(sorted(SUPPORTED_EBOOK_EXTENSIONS))
    raise ValueError(
        f"Unsupported ebook format: {extension or '(none)'}. "
        f"Supported formats: {supported}"
    )


def parse_calibre_convertible_book(
    book_path: str,
    *,
    converter_path: str | None = None,
    runner: Callable[[list[str]], object] | None = None,
    epub_parser: Callable[[str], ParsedBook] = parse_epub_book,
) -> ParsedBook:
    source = Path(book_path)
    with tempfile.TemporaryDirectory(prefix="bookvoice-calibre-") as temp_dir:
        converted_epub = Path(temp_dir) / f"{sanitize_book_folder_name(source.stem)}.epub"
        run_ebook_convert(
            source,
            converted_epub,
            executable=converter_path,
            runner=runner,
        )
        parsed = epub_parser(str(converted_epub))
    return replace(parsed, source_path=str(source))


def parse_txt_book(txt_path: str) -> ParsedBook:
    source = Path(txt_path)
    text = _read_text_file(source)
    chapters = _split_txt_chapters(text)
    metadata = BookMetadata(title=source.stem, author=UNKNOWN_AUTHOR)
    return ParsedBook(metadata=metadata, chapters=chapters, source_path=str(source))


def parse_docx_book(docx_path: str) -> ParsedBook:
    source = Path(docx_path)
    with zipfile.ZipFile(source) as archive:
        document_xml = archive.read("word/document.xml")
        core_xml = archive.read("docProps/core.xml") if "docProps/core.xml" in archive.namelist() else b""

    metadata = _extract_docx_metadata(core_xml, source)
    paragraphs = _extract_docx_paragraphs(document_xml)
    chapters = _split_structured_paragraphs(paragraphs)
    return ParsedBook(metadata=metadata, chapters=chapters, source_path=str(source))


def _read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _split_txt_chapters(text: str) -> list[ParsedChapter]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    current_title = "序章"
    current_lines: list[str] = []
    chapters: list[tuple[str, str]] = []

    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        match = TXT_CHAPTER_PATTERN.match(line)
        is_heading = bool(match) and not line.endswith(TXT_SENTENCE_ENDINGS)
        if is_heading:
            _append_txt_chapter(chapters, current_title, current_lines)
            current_title = sanitize_book_folder_name(match.group(1))
            current_lines = []
            continue
        if line:
            current_lines.append(line)

    _append_txt_chapter(chapters, current_title, current_lines)

    if not chapters and normalized.strip():
        chapters.append(("全文", " ".join(normalized.split())))

    return [
        ParsedChapter(
            index=index,
            title=title,
            text=content,
            source_id=f"txt:{index}",
            word_count=len(content),
        )
        for index, (title, content) in enumerate(chapters, 1)
    ]


def _extract_docx_metadata(core_xml: bytes, source: Path) -> BookMetadata:
    if not core_xml:
        return BookMetadata(title=source.stem, author=UNKNOWN_AUTHOR)
    root = ElementTree.fromstring(core_xml)
    title = _xml_text(root, "{http://purl.org/dc/elements/1.1/}title") or source.stem
    author = _xml_text(root, "{http://purl.org/dc/elements/1.1/}creator") or UNKNOWN_AUTHOR
    return BookMetadata(title=title, author=author)


def _xml_text(root: ElementTree.Element, tag: str) -> str:
    node = root.find(tag)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _extract_docx_paragraphs(document_xml: bytes) -> list[tuple[str, str]]:
    root = ElementTree.fromstring(document_xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[tuple[str, str]] = []

    for paragraph in root.findall(".//w:p", namespace):
        texts = [
            text_node.text or ""
            for text_node in paragraph.findall(".//w:t", namespace)
        ]
        text = "".join(texts).strip()
        if not text:
            continue
        style_node = paragraph.find(".//w:pStyle", namespace)
        style = ""
        if style_node is not None:
            style = style_node.attrib.get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val",
                "",
            )
        paragraphs.append((text, style))

    return paragraphs


def _split_structured_paragraphs(paragraphs: list[tuple[str, str]]) -> list[ParsedChapter]:
    current_title = "序章"
    current_lines: list[str] = []
    chapters: list[tuple[str, str]] = []

    for text, style in paragraphs:
        if _is_docx_heading(text, style):
            _append_txt_chapter(chapters, current_title, current_lines)
            current_title = sanitize_book_folder_name(text)
            current_lines = []
            continue
        current_lines.append(text)

    _append_txt_chapter(chapters, current_title, current_lines)

    if not chapters and paragraphs:
        content = " ".join(text for text, _style in paragraphs)
        chapters.append(("全文", " ".join(content.split())))

    return [
        ParsedChapter(
            index=index,
            title=title,
            text=content,
            source_id=f"docx:{index}",
            word_count=len(content),
        )
        for index, (title, content) in enumerate(chapters, 1)
    ]


def _is_docx_heading(text: str, style: str) -> bool:
    normalized_style = style.lower()
    if normalized_style.startswith("heading") or normalized_style.startswith("title"):
        return True
    if style in {"标题1", "标题2", "标题3"}:
        return True
    match = TXT_CHAPTER_PATTERN.match(text.strip())
    return bool(match) and not text.strip().endswith(TXT_SENTENCE_ENDINGS)


def _append_txt_chapter(
    chapters: list[tuple[str, str]],
    title: str,
    lines: list[str],
) -> None:
    content = " ".join(" ".join(lines).split())
    if content:
        chapters.append((title, content))


def _extract_metadata(book: epub.EpubBook, source: Path) -> BookMetadata:
    title = _first_metadata_value(book, "DC", "title") or source.stem
    author = _first_metadata_value(book, "DC", "creator") or UNKNOWN_AUTHOR
    language = _first_metadata_value(book, "DC", "language") or ""
    return BookMetadata(title=title, author=author, language=language)


def _first_metadata_value(book: epub.EpubBook, namespace: str, name: str) -> str:
    values = book.get_metadata(namespace, name)
    for value, _attributes in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _collect_toc_titles(toc: Iterable) -> dict[str, str]:
    titles: dict[str, str] = {}

    def visit(entry) -> None:
        if isinstance(entry, epub.Link):
            href = entry.href.split("#", 1)[0]
            if href and entry.title:
                titles[href] = entry.title.strip()
            return

        if isinstance(entry, tuple) or isinstance(entry, list):
            for child in entry:
                visit(child)
            return

        href = getattr(entry, "href", "")
        title = getattr(entry, "title", "")
        if href and title:
            titles[href.split("#", 1)[0]] = title.strip()

        for child in getattr(entry, "subitems", []) or []:
            visit(child)

    for item in toc:
        visit(item)

    return titles


def _extract_chapters(
    book: epub.EpubBook,
    toc_titles: dict[str, str],
) -> list[ParsedChapter]:
    chapters: list[ParsedChapter] = []
    for item in _spine_documents(book):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        _remove_non_content_nodes(soup)
        text = _extract_text(soup)
        if not text:
            continue

        index = len(chapters) + 1
        title = _chapter_title(item, soup, toc_titles, index)
        chapters.append(
            ParsedChapter(
                index=index,
                title=title,
                text=text,
                source_id=item.get_name(),
                word_count=len(text),
            )
        )

    return chapters


def _spine_documents(book: epub.EpubBook):
    for spine_item in book.spine:
        item_id = spine_item[0] if isinstance(spine_item, tuple) else spine_item
        item = book.get_item_with_id(item_id)
        if item is not None and item.get_type() == ebooklib.ITEM_DOCUMENT:
            yield item


def _remove_non_content_nodes(soup: BeautifulSoup) -> None:
    for node in soup(["script", "style", "nav"]):
        node.decompose()


def _extract_text(soup: BeautifulSoup) -> str:
    root = soup.body or soup
    return " ".join(root.get_text(" ", strip=True).split())


def _chapter_title(
    item,
    soup: BeautifulSoup,
    toc_titles: dict[str, str],
    index: int,
) -> str:
    item_name = item.get_name()
    title = toc_titles.get(item_name)
    if not title:
        heading = soup.find(["h1", "h2", "h3"])
        title = heading.get_text(" ", strip=True) if heading else ""
    if not title:
        title = getattr(item, "title", "") or Path(item_name).stem
    title = sanitize_book_folder_name(title)
    return title or f"第 {index} 章"
