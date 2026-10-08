"""Integration test: batch parameter edit + STEP/PDF export."""

import os
import tempfile
import unittest

from solidworks_mcp import runtime


class BatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = runtime.get_session(visible=True)
        cls.modeling = runtime.get_modeling()
        cls.batch = runtime.get_batch()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def test_edit_depth_and_export(self):
        workdir = tempfile.mkdtemp(prefix="sw_batch_")
        title = self.session.new_document("part")
        try:
            self.modeling.sketch_rectangle("front", -50, -30, 50, 30)
            self.modeling.extrude(8.0)

            # Depth parameter is stored in metres; read back in mm.
            depth = self.batch.get_parameter("D1@凸台-拉伸1")
            self.assertIsNotNone(depth)
            self.assertAlmostEqual(depth, 8.0, delta=0.01)

            # Change depth to 12 mm -> volume becomes 100 x 60 x 12.
            self.batch.set_parameter("D1@凸台-拉伸1", 12.0)
            props = self.modeling.mass_properties(1000.0)
            self.assertAlmostEqual(props["volume_mm3"], 72000.0, delta=50.0)

            step_path = os.path.join(workdir, "plate.step")
            self.batch.export(step_path)
            self.assertTrue(os.path.exists(step_path))
            self.assertGreater(os.path.getsize(step_path), 0)

            pdf_path = os.path.join(workdir, "plate.pdf")
            self.batch.export(pdf_path)
            self.assertTrue(os.path.exists(pdf_path))
        finally:
            self.session.close(title)


if __name__ == "__main__":
    unittest.main()
