import unittest

from bookvoice.book import ParsedChapter
from bookvoice.chapter_selection import ChapterSelection


class ChapterSelectionTests(unittest.TestCase):
    def test_load_selects_all_chapters_by_default(self):
        selection = ChapterSelection()

        selection.load(
            [
                ParsedChapter(1, "第一章", "内容", "1"),
                ParsedChapter(2, "第二章", "内容", "2"),
            ]
        )

        self.assertEqual(selection.selected_indexes(), (1, 2))
        self.assertTrue(selection.is_selected(1))

    def test_toggle_switches_single_chapter_selection(self):
        selection = ChapterSelection()
        selection.load(
            [
                ParsedChapter(1, "第一章", "内容", "1"),
                ParsedChapter(2, "第二章", "内容", "2"),
            ]
        )

        self.assertFalse(selection.toggle(2))
        self.assertEqual(selection.selected_indexes(), (1,))
        self.assertTrue(selection.toggle(2))
        self.assertEqual(selection.selected_indexes(), (1, 2))


if __name__ == "__main__":
    unittest.main()

