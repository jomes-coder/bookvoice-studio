import unittest

from bookvoice.task_queue import CANCELED, TaskQueue


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


if __name__ == "__main__":
    unittest.main()

