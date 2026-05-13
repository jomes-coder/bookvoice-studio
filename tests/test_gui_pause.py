import asyncio
import unittest

from bookvoice.gui import CancelController, PauseController


class PauseControllerTests(unittest.TestCase):
    def test_toggle_pause_and_resume_updates_state_and_button_text(self):
        controller = PauseController()

        paused = controller.toggle()
        self.assertTrue(controller.is_paused)
        self.assertFalse(controller.event.is_set())
        self.assertEqual(paused.button_text, "继续")
        self.assertIn("已暂停", paused.log_message)

        resumed = controller.toggle()
        self.assertFalse(controller.is_paused)
        self.assertTrue(controller.event.is_set())
        self.assertEqual(resumed.button_text, "暂停")
        self.assertIn("继续转换", resumed.log_message)

    def test_wait_while_paused_blocks_until_resumed(self):
        async def run_test():
            controller = PauseController()
            controller.pause()

            waiter = asyncio.create_task(controller.wait_while_paused(0.01))
            await asyncio.sleep(0.03)
            self.assertFalse(waiter.done())

            controller.resume()
            await asyncio.wait_for(waiter, timeout=1)

        asyncio.run(run_test())


class CancelControllerTests(unittest.TestCase):
    def test_cancel_controller_tracks_requested_state(self):
        controller = CancelController()

        self.assertFalse(controller.is_cancel_requested())
        controller.request_cancel()
        self.assertTrue(controller.is_cancel_requested())
        controller.reset()
        self.assertFalse(controller.is_cancel_requested())


if __name__ == "__main__":
    unittest.main()

