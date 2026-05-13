import importlib
import os
import sys
import unittest


class GuiImportTests(unittest.TestCase):
    def test_gui_module_exposes_launch_function_without_creating_window(self):
        module = importlib.import_module("bookvoice.gui")

        self.assertTrue(callable(module.main))
        self.assertTrue(hasattr(module, "BookVoiceStudioApp"))
        self.assertTrue(hasattr(module, "Epub2Mp3App"))

    def test_gui_module_configures_tcl_paths_when_available(self):
        os.environ.pop("TCL_LIBRARY", None)
        os.environ.pop("TK_LIBRARY", None)
        sys.modules.pop("bookvoice.gui", None)

        importlib.import_module("bookvoice.gui")

        self.assertTrue(os.environ["TCL_LIBRARY"].endswith(os.path.join("tcl", "tcl8.6")))
        self.assertTrue(os.environ["TK_LIBRARY"].endswith(os.path.join("tcl", "tk8.6")))


if __name__ == "__main__":
    unittest.main()

