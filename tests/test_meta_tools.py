"""Integration test for the session/meta MCP tools (called directly, no stdio)."""

import os
import tempfile
import unittest

from solidworks_mcp import runtime, server


class MetaToolsTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def test_connect_and_version(self):
        res = server.sw_connect(visible=True)
        self.assertTrue(res["ok"])
        self.assertTrue(server.sw_version()["revision"].startswith("30"))

    def test_new_part_screenshot_close(self):
        server.sw_connect(visible=True)
        title = server.sw_new_part()["title"]
        self.assertTrue(title)
        self.assertIn(title, server.sw_list_documents()["titles"])

        out_dir = tempfile.mkdtemp(prefix="sw_shot_")
        shot = server.sw_screenshot(os.path.join(out_dir, "shot.bmp"))["path"]
        self.assertTrue(os.path.exists(shot))

        self.assertTrue(server.sw_close(title)["closed"])
        self.assertNotIn(title, server.sw_list_documents()["titles"])


if __name__ == "__main__":
    unittest.main()
