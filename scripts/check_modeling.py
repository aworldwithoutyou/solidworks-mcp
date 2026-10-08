"""Acceptance check: build a plate from natural-language-like parameters.

Plate 100 x 60 x 8 mm, four phi6 through holes, 2 mm chamfer on the four
vertical corner edges.

Usage (from the project root, with the venv):

    .venv\\Scripts\\python.exe scripts\\check_modeling.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solidworks_mcp import runtime  # noqa: E402


def main() -> int:
    session = runtime.get_session(visible=True)
    modeling = runtime.get_modeling()
    session.connect()

    title = session.new_document("part")
    print("part:", title, flush=True)

    modeling.sketch_rectangle("front", -50, -30, 50, 30)
    print("extrude:", modeling.extrude(8.0), flush=True)

    circles = [(-40, -20, 3), (40, -20, 3), (40, 20, 3), (-40, 20, 3)]
    modeling.sketch_circles("front", circles)
    print("cut:", modeling.extrude_cut(20.0, through_all=False), flush=True)

    modeling.clear_selection()
    for x, y in ((-50, -30), (50, -30), (50, 30), (-50, 30)):
        ok = modeling.select_at(x, y, 4.0, "EDGE", append=True)
        print(f"  select edge ({x},{y}) -> {ok}", flush=True)
    print("chamfer:", modeling.chamfer(2.0), flush=True)

    def _props():
        doc = session.require_sw().ActiveDoc
        bodies = doc.GetBodies2(0, True)
        if not bodies:
            return None
        mp = bodies[0].GetMassProperties(1000.0)
        return list(mp) if mp is not None else None

    print("mass props:", session.worker.call(_props), flush=True)

    session.save_screenshot(os.path.join(os.environ.get("TEMP", "."), "plate.bmp"))
    print("done", flush=True)
    session.close(title)
    runtime.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
