import tempfile
import unittest
from pathlib import Path

from bookvoice.task_queue import (
    CANCELED,
    PENDING,
    TaskQueue,
    load_task_queue,
    save_task_queue,
    task_queue_state_path,
)


class TaskQueueTests(unittest.TestCase):
    def test_add_many_deduplicates_paths_and_preserves_order(self):
        queue = TaskQueue()

        added_count = queue.add_many(["a.epub", "b.txt", "a.epub"])

        self.assertEqual(added_count, 2)
        self.assertEqual(queue.paths(), ("a.epub", "b.txt"))
        self.assertEqual(queue.pending_paths(), ("a.epub", "b.txt"))

    def test_mark_statuses_and_next_pending(self):
        queue = TaskQueue()
        queue.add_many(["a.epub", "b.txt"])

        self.assertEqual(queue.next_pending(), "a.epub")
        queue.mark_running("a.epub")
        queue.mark_completed("a.epub")
        queue.mark_failed("b.txt")

        self.assertEqual(queue.status("a.epub"), "completed")
        self.assertEqual(queue.status("b.txt"), "failed")
        self.assertIsNone(queue.next_pending())

    def test_status_counts_include_pending_running_completed_failed_and_canceled(self):
        queue = TaskQueue()
        queue.add_many(["a.epub", "b.txt", "c.docx", "d.epub", "e.txt"])
        queue.mark_running("a.epub")
        queue.mark_completed("b.txt")
        queue.mark_failed("c.docx")
        queue.mark_canceled("d.epub")

        self.assertEqual(
            queue.status_counts(),
            {
                "pending": 1,
                "running": 1,
                "completed": 1,
                "failed": 1,
                CANCELED: 1,
            },
        )

    def test_snapshot_roundtrip_resets_running_task_to_pending_for_resume(self):
        queue = TaskQueue()
        queue.add_many(["a.epub", "b.txt"])
        queue.mark_running("a.epub")
        queue.mark_canceled("b.txt")

        restored = TaskQueue.from_records(queue.to_records())

        self.assertEqual(restored.paths(), ("a.epub", "b.txt"))
        self.assertEqual(restored.status("a.epub"), PENDING)
        self.assertEqual(restored.status("b.txt"), CANCELED)
        self.assertEqual(restored.pending_paths(), ("a.epub",))

    def test_save_and_load_task_queue_roundtrip_uses_state_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            queue = TaskQueue()
            queue.add_many(["D:\\books\\a.epub", "D:\\books\\b.txt"])
            queue.mark_running("D:\\books\\a.epub")

            save_task_queue(queue, state_dir)
            loaded = load_task_queue(state_dir)

            self.assertEqual(task_queue_state_path(state_dir).name, "task_queue.json")
            self.assertEqual(loaded.paths(), ("D:\\books\\a.epub", "D:\\books\\b.txt"))
            self.assertEqual(loaded.status("D:\\books\\a.epub"), PENDING)
            self.assertEqual(loaded.status("D:\\books\\b.txt"), PENDING)

    def test_load_task_queue_ignores_corrupt_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            task_queue_state_path(state_dir).write_text("{bad json", encoding="utf-8")

            loaded = load_task_queue(state_dir)

        self.assertEqual(loaded.paths(), ())


if __name__ == "__main__":
    unittest.main()

