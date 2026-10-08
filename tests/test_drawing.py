"""Integration test: part -> drawing with views/annotations -> PDF export."""

import os
import tempfile
import unittest

from solidworks_mcp import runtime


class DrawingIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = runtime.get_session(visible=True)
        cls.modeling = runtime.get_modeling()
        cls.drawing = runtime.get_drawing()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def test_plate_to_annotated_pdf(self):
        workdir = tempfile.mkdtemp(prefix="sw_draw_")
        part_path = os.path.join(workdir, "plate.sldprt")
        pdf_path = os.path.join(workdir, "plate.pdf")

        part_title = self.session.new_document("part")
        try:
            self.modeling.sketch_rectangle("front", -50, -30, 50, 30)
            self.assertTrue(self.modeling.extrude(8.0))
            self.session.save(part_path)
        finally:
            self.session.close(part_title)

        draw_title = self.drawing.new_drawing()
        try:
            for view, x in (("front", 0.05), ("top", 0.15), ("right", 0.25), ("isometric", 0.35)):
                self.assertTrue(self.drawing.create_view(part_path, view, x, 0.15))
            self.drawing.insert_model_annotations(True)
            self.drawing.export(pdf_path)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)
        finally:
            self.session.close(draw_title)


if __name__ == "__main__":
    unittest.main()
