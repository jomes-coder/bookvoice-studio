import importlib
import unittest


class BrandingTests(unittest.TestCase):
    def test_bookvoice_branding_constants_describe_public_product(self):
        branding = importlib.import_module("bookvoice.branding")

        self.assertEqual(branding.PRODUCT_NAME, "BookVoice Studio")
        self.assertEqual(branding.PRODUCT_NAME_CN, "书声工坊")
        self.assertEqual(branding.PROJECT_SLUG, "bookvoice-studio")
        self.assertEqual(branding.APP_STATE_DIR_NAME, "BookVoiceStudio")
        self.assertEqual(branding.DIST_APP_NAME, "BookVoiceStudio")
        self.assertEqual(branding.LEGACY_PROJECT_NAME, "epub2mp3")

    def test_new_package_and_legacy_package_import_same_cli_entry(self):
        new_main = importlib.import_module("bookvoice.main")
        legacy_main = importlib.import_module("epub2mp3.main")

        self.assertIs(legacy_main.build_parser, new_main.build_parser)


if __name__ == "__main__":
    unittest.main()
