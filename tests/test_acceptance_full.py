"""End-to-end acceptance: part -> annotated drawing PDF + batch parameter edit/export."""

import os
import tempfile
import unittest

from solidworks_mcp import runtime


class FullAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = runtime.get_session(visible=True)
        cls.modeling = runtime.get_modeling()
        cls.drawing = runtime.get_drawing()
        cls.batch = runtime.get_batch()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def test_plate_to_drawing_and_batch(self):
        workdir = tempfile.mkdtemp(prefix="sw_e2e_")
        part_path = os.path.join(workdir, "plate.sldprt")
        pdf_path = os.path.join(workdir, "plate.pdf")
        step_path = os.path.join(workdir, "plate.step")

        # --- part: 100 x 60 x 8 with four phi6 holes ---
        part_title = self.session.new_document("part")
        self.modeling.sketch_rectangle("front", -50, -30, 50, 30)
        self.assertTrue(self.modeling.extrude(8.0))
        self.modeling.sketch_circles(
            "front", [(-40, -20, 3), (40, -20, 3), (40, 20, 3), (-40, 20, 3)]
        )
        self.assertTrue(self.modeling.extrude_cut(20.0, through_all=False))
        self.session.save(part_path)
        self.session.close(part_title)

        # --- drawing: views + model annotations -> PDF ---
        draw_title = self.drawing.new_drawing()
        try:
            for view, x in (
                ("front", 0.05), ("top", 0.15), ("right", 0.25), ("isometric", 0.35)
            ):
                self.assertTrue(self.drawing.create_view(part_path, view, x, 0.15))
            self.drawing.insert_model_annotations(True)
            self.drawing.export(pdf_path)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)
        finally:
            self.session.close(draw_title)

        # --- batch: reopen part, change depth, export STEP ---
        part_title2 = self.session.open_document(part_path, "part")
        try:
            self.batch.set_parameter("D1@凸台-拉伸1", 12.0)
            self.batch.export(step_path)
            self.assertTrue(os.path.exists(step_path))
            self.assertGreater(os.path.getsize(step_path), 0)
        finally:
            self.session.close(part_title2)


if __name__ == "__main__":
    unittest.main()
