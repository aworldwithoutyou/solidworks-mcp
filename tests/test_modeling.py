"""Integration test for the rebuild / mass-properties / screenshot loop."""

import os
import tempfile
import unittest

from solidworks_mcp import runtime


class ModelingInspectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = runtime.get_session(visible=True)
        cls.modeling = runtime.get_modeling()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def test_plate_rebuild_mass_and_screenshot(self):
        title = self.session.new_document("part")
        try:
            self.modeling.sketch_rectangle("front", -50, -30, 50, 30)
            feat = self.modeling.extrude(8.0)
            self.assertTrue(feat)

            self.modeling.rebuild()
            props = self.modeling.mass_properties(1000.0)
            # 100 x 60 x 8 mm solid block.
            self.assertEqual(props["bodies"], 1)
            self.assertAlmostEqual(props["volume_mm3"], 48000.0, delta=50.0)

            out = os.path.join(tempfile.gettempdir(), "test_modeling.bmp")
            shot = self.session.save_screenshot(out)
            self.assertTrue(os.path.exists(shot))
        finally:
            self.session.close(title)


if __name__ == "__main__":
    unittest.main()
