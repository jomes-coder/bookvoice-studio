import unittest

from bookvoice.gui import (
    ACCENT_BUTTON_PADDING,
    BASE_BUTTON_PADDING,
    CALIBRE_DOWNLOAD_URL,
    CALIBRE_ROW_COLUMNS,
    CHAPTER_TREE_COLUMNS,
    CHAPTER_TREE_COLUMN_WIDTHS,
    CHAPTER_TITLE_DISPLAY_LIMIT,
    CHAPTER_STATUS_LABELS,
    CHAPTER_STATUS_PENDING,
    CONTROL_BUTTON_GAP,
    CONTROL_BUTTON_LAYOUT,
    CONTROL_BUTTON_COLUMNS,
    CONTROL_BUTTON_TEXTS,
    COVER_FILE_TYPES,
    EBOOK_FILE_TYPES,
    FILE_ENTRY_WIDTH,
    FILE_ROW_COLUMNS,
    PRODUCT_OPTION_LAYOUT,
    QUEUE_BUTTON_COLUMNS,
    QUEUE_BUTTON_TEXTS,
    QUEUE_TREE_COLUMNS,
    SECONDARY_BUTTON_PADDING,
    chapter_row_values,
    format_chapter_title_for_preview,
    format_queue_summary,
    queue_display_rows,
    SETTINGS_LAYOUT_ROWS,
    SPEECH_PITCH_OPTIONS,
    SPEECH_RATE_OPTIONS,
    SPEECH_VOLUME_OPTIONS,
    WORKSPACE_TAB_LABELS,
    WORKSPACE_TABS,
    open_calibre_download_page,
)
from bookvoice.task_queue import TaskQueue
from bookvoice.book import ParsedChapter


class GuiLayoutTests(unittest.TestCase):
    def test_settings_rows_do_not_overlap(self):
        ordered_rows = [
            SETTINGS_LAYOUT_ROWS["section"],
            SETTINGS_LAYOUT_ROWS["epub"],
            SETTINGS_LAYOUT_ROWS["calibre"],
            SETTINGS_LAYOUT_ROWS["voice"],
            SETTINGS_LAYOUT_ROWS["speech"],
            SETTINGS_LAYOUT_ROWS["output"],
            SETTINGS_LAYOUT_ROWS["background"],
            SETTINGS_LAYOUT_ROWS["cover"],
            SETTINGS_LAYOUT_ROWS["product"],
            SETTINGS_LAYOUT_ROWS["numeric"],
            SETTINGS_LAYOUT_ROWS["progress"],
            SETTINGS_LAYOUT_ROWS["start"],
        ]
        self.assertEqual(ordered_rows, sorted(ordered_rows))
        self.assertEqual(len(ordered_rows), len(set(ordered_rows)))

    def test_speech_option_defaults_are_available_for_gui_controls(self):
        self.assertIn("+0%", SPEECH_RATE_OPTIONS)
        self.assertIn("+0%", SPEECH_VOLUME_OPTIONS)
        self.assertIn("+0Hz", SPEECH_PITCH_OPTIONS)

    def test_file_picker_includes_supported_ebook_formats(self):
        file_type_text = " ".join(pattern for _label, pattern in EBOOK_FILE_TYPES)

        self.assertIn("*.epub", file_type_text)
        self.assertIn("*.txt", file_type_text)
        self.assertIn("*.docx", file_type_text)
        self.assertIn("*.mobi", file_type_text)
        self.assertIn("*.azw3", file_type_text)

    def test_cover_file_picker_includes_common_image_formats(self):
        file_type_text = " ".join(pattern for _label, pattern in COVER_FILE_TYPES)

        self.assertIn("*.jpg", file_type_text)
        self.assertIn("*.jpeg", file_type_text)
        self.assertIn("*.png", file_type_text)

    def test_retry_button_has_distinct_control_column(self):
        self.assertLess(CONTROL_BUTTON_COLUMNS["start"], CONTROL_BUTTON_COLUMNS["pause"])
        self.assertLess(CONTROL_BUTTON_COLUMNS["pause"], CONTROL_BUTTON_COLUMNS["cancel"])
        self.assertLess(CONTROL_BUTTON_COLUMNS["cancel"], CONTROL_BUTTON_COLUMNS["retry"])
        self.assertLess(CONTROL_BUTTON_COLUMNS["retry"], CONTROL_BUTTON_COLUMNS["open_output"])
        self.assertLess(CONTROL_BUTTON_COLUMNS["open_output"], CONTROL_BUTTON_COLUMNS["check_env"])
        self.assertLess(CONTROL_BUTTON_COLUMNS["check_env"], CONTROL_BUTTON_COLUMNS["guide"])

    def test_control_buttons_are_split_into_primary_and_utility_rows(self):
        self.assertEqual(CONTROL_BUTTON_LAYOUT["start"], (0, 0))
        self.assertEqual(CONTROL_BUTTON_LAYOUT["pause"], (0, 1))
        self.assertEqual(CONTROL_BUTTON_LAYOUT["cancel"], (0, 2))
        self.assertEqual(CONTROL_BUTTON_LAYOUT["retry"], (1, 0))
        self.assertEqual(CONTROL_BUTTON_LAYOUT["open_output"], (1, 1))
        self.assertEqual(CONTROL_BUTTON_LAYOUT["check_env"], (1, 2))
        self.assertEqual(CONTROL_BUTTON_LAYOUT["guide"], (1, 3))

    def test_buttons_use_compact_padding_and_short_labels(self):
        self.assertLessEqual(BASE_BUTTON_PADDING, (8, 4))
        self.assertLessEqual(SECONDARY_BUTTON_PADDING, (9, 5))
        self.assertLessEqual(ACCENT_BUTTON_PADDING, (10, 6))
        self.assertLessEqual(CONTROL_BUTTON_GAP, 6)

        for label in CONTROL_BUTTON_TEXTS.values():
            self.assertLessEqual(len(label), 4)
        for label in QUEUE_BUTTON_TEXTS.values():
            self.assertLessEqual(len(label), 4)

    def test_calibre_path_row_is_between_ebook_and_voice_rows(self):
        self.assertLess(SETTINGS_LAYOUT_ROWS["epub"], SETTINGS_LAYOUT_ROWS["calibre"])
        self.assertLess(SETTINGS_LAYOUT_ROWS["calibre"], SETTINGS_LAYOUT_ROWS["voice"])

    def test_workspace_tabs_separate_chapters_queue_and_logs(self):
        self.assertEqual(WORKSPACE_TABS, ("chapters", "queue", "logs"))
        self.assertEqual(WORKSPACE_TAB_LABELS["chapters"], "章节预览")
        self.assertEqual(WORKSPACE_TAB_LABELS["queue"], "批量队列")
        self.assertEqual(WORKSPACE_TAB_LABELS["logs"], "转换日志")

    def test_product_options_are_compacted_into_two_rows(self):
        self.assertEqual(PRODUCT_OPTION_LAYOUT["mp3_metadata"], (0, 0))
        self.assertEqual(PRODUCT_OPTION_LAYOUT["m4b"], (0, 1))
        self.assertEqual(PRODUCT_OPTION_LAYOUT["overwrite"], (0, 2))
        self.assertEqual(PRODUCT_OPTION_LAYOUT["high_quality"], (1, 0))
        self.assertEqual(PRODUCT_OPTION_LAYOUT["lyrics"], (1, 1))

    def test_chapter_tree_columns_support_preview_selection(self):
        self.assertEqual(
            CHAPTER_TREE_COLUMNS,
            ("selected", "index", "status", "title", "word_count"),
        )

    def test_chapter_status_labels_are_chinese_and_fit_status_column(self):
        self.assertEqual(CHAPTER_STATUS_LABELS[CHAPTER_STATUS_PENDING], "待转换")
        self.assertGreaterEqual(CHAPTER_TREE_COLUMN_WIDTHS["status"], 72)
        self.assertFalse(CHAPTER_TREE_COLUMN_WIDTHS["status_stretch"])

    def test_chapter_row_values_include_status_label(self):
        chapter = ParsedChapter(
            index=1,
            title="第一章",
            text="正文",
            source_id="chapter.xhtml",
            word_count=2,
        )

        self.assertEqual(
            chapter_row_values(chapter),
            ("是", 1, "待转换", "第一章", 2),
        )

    def test_chapter_preview_truncates_long_titles_but_keeps_short_titles(self):
        short_title = "第一章"
        long_title = "第一章 " + "很长的章节标题" * 12

        self.assertEqual(format_chapter_title_for_preview(short_title), short_title)
        truncated = format_chapter_title_for_preview(long_title)

        self.assertLessEqual(len(truncated), CHAPTER_TITLE_DISPLAY_LIMIT)
        self.assertTrue(truncated.endswith("..."))

    def test_chapter_word_count_column_has_fixed_readable_width(self):
        self.assertGreaterEqual(CHAPTER_TREE_COLUMN_WIDTHS["word_count"], 92)
        self.assertFalse(CHAPTER_TREE_COLUMN_WIDTHS["word_count_stretch"])

    def test_queue_tree_columns_support_batch_status(self):
        self.assertEqual(
            QUEUE_TREE_COLUMNS,
            ("index", "status", "name", "path"),
        )

    def test_file_rows_use_one_line_with_shorter_text_entry(self):
        self.assertEqual(FILE_ROW_COLUMNS["label"], 0)
        self.assertEqual(FILE_ROW_COLUMNS["entry"], 1)
        self.assertEqual(FILE_ROW_COLUMNS["browse"], 3)
        self.assertEqual(FILE_ROW_COLUMNS["clear"], 4)
        self.assertLessEqual(FILE_ENTRY_WIDTH, 28)

    def test_calibre_row_has_download_button_after_browse_button(self):
        self.assertEqual(CALIBRE_ROW_COLUMNS["label"], 0)
        self.assertEqual(CALIBRE_ROW_COLUMNS["entry"], 1)
        self.assertLess(CALIBRE_ROW_COLUMNS["browse"], CALIBRE_ROW_COLUMNS["download"])
        self.assertLess(CALIBRE_ROW_COLUMNS["download"], CALIBRE_ROW_COLUMNS["clear"])

    def test_calibre_download_button_opens_official_download_page(self):
        opened_urls = []

        def opener(url):
            opened_urls.append(url)
            return True

        result = open_calibre_download_page(opener)

        self.assertTrue(result)
        self.assertEqual(opened_urls, [CALIBRE_DOWNLOAD_URL])
        self.assertEqual(CALIBRE_DOWNLOAD_URL, "https://www.calibre-ebook.com/download_windows64")

    def test_queue_buttons_have_distinct_columns(self):
        self.assertLess(QUEUE_BUTTON_COLUMNS["add"], QUEUE_BUTTON_COLUMNS["start"])
        self.assertLess(QUEUE_BUTTON_COLUMNS["start"], QUEUE_BUTTON_COLUMNS["clear"])

    def test_queue_summary_uses_chinese_status_counts(self):
        queue = TaskQueue()
        queue.add_many(["D:\\books\\a.epub", "D:\\books\\b.txt"])
        queue.mark_running("D:\\books\\a.epub")

        self.assertEqual(
            format_queue_summary(queue),
            "队列：共 2 本，待转换 1，转换中 1，已完成 0，失败 0，已取消 0",
        )

    def test_queue_display_rows_show_index_status_name_and_path(self):
        queue = TaskQueue()
        queue.add_many(["D:\\books\\a.epub"])

        self.assertEqual(
            queue_display_rows(queue),
            [(1, "待转换", "a.epub", "D:\\books\\a.epub")],
        )


if __name__ == "__main__":
    unittest.main()

