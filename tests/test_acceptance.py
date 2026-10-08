"""Acceptance test: natural-language plate -> model -> dimension/mass check.

Plate 100 x 60 x 8 mm, four phi6 through holes, 2 mm chamfer. Volume is checked
at each step against the analytic value.
"""

import math
import os
import tempfile
import unittest

from solidworks_mcp import runtime


class PlateAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = runtime.get_session(visible=True)
        cls.m = runtime.get_modeling()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def test_plate_dimensions_and_mass(self):
        title = self.session.new_document("part")
        try:
            # 100 x 60 x 8 solid block.
            self.m.sketch_rectangle("front", -50, -30, 50, 30)
            self.assertTrue(self.m.extrude(8.0))
            props = self.m.mass_properties(1000.0)
            self.assertAlmostEqual(props["volume_mm3"], 48000.0, delta=40.0)

            # Four phi6 through holes.
            self.m.sketch_circles(
                "front", [(-40, -20, 3), (40, -20, 3), (40, 20, 3), (-40, 20, 3)]
            )
            self.assertTrue(self.m.extrude_cut(20.0, through_all=False))
            props = self.m.mass_properties(1000.0)
            expected = 48000.0 - 4 * math.pi * 9 * 8
            self.assertAlmostEqual(props["volume_mm3"], expected, delta=40.0)

            # 2 mm chamfer on the four vertical corner edges.
            self.m.clear_selection()
            for x, y in ((-50, -30), (50, -30), (50, 30), (-50, 30)):
                self.m.select_at(x, y, 4.0, "EDGE", append=True)
            self.m.chamfer(2.0)
            props = self.m.mass_properties(1000.0)
            self.assertLess(props["volume_mm3"], expected)

            shot = self.session.save_screenshot(
                os.path.join(tempfile.gettempdir(), "plate_accept.bmp")
            )
            self.assertTrue(os.path.exists(shot))
        finally:
            self.session.close(title)


if __name__ == "__main__":
    unittest.main()
