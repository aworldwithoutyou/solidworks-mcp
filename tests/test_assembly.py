"""Integration test: assembly components + exploded view.

Mate and interference-count APIs live on vtable-only interfaces that pywin32
cannot early-bind for SolidWorks, so they are implemented but not asserted here
(see assembly.py docstrings).
"""

import os
import tempfile
import unittest

from solidworks_mcp import runtime


class AssemblyIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = runtime.get_session(visible=True)
        cls.modeling = runtime.get_modeling()
        cls.assembly = runtime.get_assembly()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        runtime.shutdown()

    def _make_block(self, workdir, name, size=20.0):
        title = self.session.new_document("part")
        path = os.path.join(workdir, name)
        self.modeling.sketch_rectangle(
            "front", -size / 2, -size / 2, size / 2, size / 2
        )
        self.assertTrue(self.modeling.extrude(size))
        self.session.save(path)
        self.session.close(title)
        return path

    def test_components_and_exploded_view(self):
        workdir = tempfile.mkdtemp(prefix="sw_asm_")
        block_a = self._make_block(workdir, "a.sldprt")
        block_b = self._make_block(workdir, "b.sldprt")

        asm_title = self.assembly.new_assembly()
        try:
            comp_a = self.assembly.add_component(block_a, 0, 0, 0)
            comp_b = self.assembly.add_component(block_b, 0, 0, 25)
            self.assertTrue(comp_a)
            self.assertTrue(comp_b)

            self.assertTrue(self.assembly.create_exploded_view())
        finally:
            self.session.close(asm_title)


if __name__ == "__main__":
    unittest.main()
