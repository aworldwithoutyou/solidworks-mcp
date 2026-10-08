"""Integration test for the STA worker + session layer.

Requires a working SolidWorks 2022 installation; connects, creates a part,
checks document tracking, and closes it. Run with the project venv:

    .venv\\Scripts\\python.exe -m unittest tests.test_session -v
"""

import unittest

from solidworks_mcp.com.session import SolidWorksSession
from solidworks_mcp.com.worker import ComWorker


class SessionIntegrationTest(unittest.TestCase):
    worker: ComWorker
    session: SolidWorksSession

    @classmethod
    def setUpClass(cls):
        cls.worker = ComWorker()
        cls.session = SolidWorksSession(cls.worker, visible=True)
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        cls.worker.stop()

    def test_revision_is_2022_family(self):
        rev = self.session.revision()
        self.assertTrue(rev.startswith("30"), f"unexpected revision {rev!r}")

    def test_new_part_tracking_and_close(self):
        title = self.session.new_document("part")
        self.assertTrue(title)
        self.assertIn(title, self.session.list_open_documents())
        self.assertEqual(self.session.active_title(), title)
        self.assertTrue(self.session.close(title))
        self.assertNotIn(title, self.session.list_open_documents())


if __name__ == "__main__":
    unittest.main()
