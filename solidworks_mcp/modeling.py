"""Parameterized part modeling: sketches and features.

Lengths cross this API boundary in millimetres and are converted to metres
(SolidWorks' internal unit). All COM work runs on the session's STA thread.
Methods act on the active document and on the current selection, mirroring the
SolidWorks workflow (select, then apply a feature).
"""

from __future__ import annotations

import math
from typing import Optional

import pythoncom
from win32com.client import VARIANT

from .com.session import SolidWorksSession

MM = 0.001

# swEndConditions_e
END_BLIND = 0
END_THROUGH_ALL = 1
END_THROUGH_ALL_BOTH = 2

# swFeatureFilletOptions_e (combined)
FILLET_UNIFORM_RADIUS = 1
FILLET_PROPAGATE = 2

# swChamferType_e
CHAMFER_ANGLE_DISTANCE = 0
CHAMFER_EQUAL_DISTANCE = 1

# Default GB plane names (localized) with English/Chinese aliases.
PLANE_ALIASES = {
    "front": "前视基准面",
    "top": "上视基准面",
    "right": "右视基准面",
    "前视": "前视基准面",
    "上视": "上视基准面",
    "右视": "右视基准面",
    "前视基准面": "前视基准面",
    "上视基准面": "上视基准面",
    "右视基准面": "右视基准面",
}


def _null_callout() -> VARIANT:
    return VARIANT(pythoncom.VT_DISPATCH, None)


def _resolve_plane(plane: str) -> str:
    return PLANE_ALIASES.get(plane, plane)


def _name_of(feature) -> Optional[str]:
    if feature is None:
        return None
    try:
        return feature.Name
    except Exception:  # noqa: BLE001 - some methods return void
        return None


class Modeling:
    def __init__(self, session: SolidWorksSession) -> None:
        self._session = session
        self._worker = session.worker

    def _doc(self):
        doc = self._session.require_sw().ActiveDoc
        if doc is None:
            raise RuntimeError("No active document.")
        return doc

    # -- selection ----------------------------------------------------------
    def clear_selection(self) -> None:
        def _do():
            self._doc().ClearSelection2(True)

        self._worker.call(_do)

    def select(self, name: str, type_: str, append: bool = False, mark: int = 0) -> bool:
        def _do():
            doc = self._doc()
            return bool(
                doc.Extension.SelectByID2(
                    name, type_, 0, 0, 0, append, mark, _null_callout(), 0
                )
            )

        return self._worker.call(_do)

    def select_at(
        self, x: float, y: float, z: float, type_: str = "EDGE",
        append: bool = True, mark: int = 0,
    ) -> bool:
        """Select the entity nearest a point (mm); useful when names are unknown."""
        def _do():
            doc = self._doc()
            return bool(
                doc.Extension.SelectByID2(
                    "", type_, x * MM, y * MM, z * MM, append, mark, _null_callout(), 0
                )
            )

        return self._worker.call(_do)

    # -- sketches -----------------------------------------------------------
    def _begin_sketch(self, doc, plane: str) -> None:
        ok = doc.Extension.SelectByID2(
            _resolve_plane(plane), "PLANE", 0, 0, 0, False, 0, _null_callout(), 0
        )
        if not ok:
            raise RuntimeError(f"Could not select plane {plane!r}.")
        doc.SketchManager.InsertSketch(True)

    def _end_sketch(self, doc) -> Optional[str]:
        doc.SketchManager.InsertSketch(True)
        try:
            sk = doc.GetActiveSketch2()
            return sk.Name if sk is not None else None
        except Exception:  # noqa: BLE001
            return None

    def sketch_rectangle(
        self, plane: str, x1: float, y1: float, x2: float, y2: float
    ) -> Optional[str]:
        def _do():
            doc = self._doc()
            self._begin_sketch(doc, plane)
            doc.SketchManager.CreateCornerRectangle(
                x1 * MM, y1 * MM, 0.0, x2 * MM, y2 * MM, 0.0
            )
            return self._end_sketch(doc)

        return self._worker.call(_do)

    def sketch_circle(
        self, plane: str, cx: float, cy: float, radius: float
    ) -> Optional[str]:
        def _do():
            doc = self._doc()
            self._begin_sketch(doc, plane)
            doc.SketchManager.CreateCircleByRadius(
                cx * MM, cy * MM, 0.0, radius * MM
            )
            return self._end_sketch(doc)

        return self._worker.call(_do)

    def sketch_circles(
        self, plane: str, circles: "list[tuple[float, float, float]]"
    ) -> Optional[str]:
        """Create several circles (cx, cy, radius in mm) in a single sketch."""
        def _do():
            doc = self._doc()
            self._begin_sketch(doc, plane)
            for cx, cy, radius in circles:
                doc.SketchManager.CreateCircleByRadius(
                    cx * MM, cy * MM, 0.0, radius * MM
                )
            return self._end_sketch(doc)

        return self._worker.call(_do)

    # -- features (act on the current selection) ----------------------------
    def extrude(
        self, depth: float, through_all: bool = False, flip: bool = False
    ) -> Optional[str]:
        end = END_THROUGH_ALL if through_all else END_BLIND

        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.FeatureExtrusion3(
                True, False, flip, end, 0, depth * MM, 0,
                False, False, False, False, 0, 0,
                False, False, False, False, True, True, True, 0, 0, False,
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def extrude_cut(
        self, depth: float, through_all: bool = True, flip: bool = False
    ) -> Optional[str]:
        end = END_THROUGH_ALL if through_all else END_BLIND

        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.FeatureCut4(
                True, flip, True, end, 0, depth * MM, 0,
                False, False, False, False, 0, 0,
                False, False, False, False, False, True, True,
                False, False, False, 0, 0, False, True,
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def revolve(self, angle_deg: float = 360.0, is_cut: bool = False) -> Optional[str]:
        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.FeatureRevolve2(
                True, True, False, is_cut, False, False, 0, 0,
                math.radians(angle_deg), 0, False, False, 0, 0,
                0, 0, 0, True, True, True,
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def fillet(self, radius: float, propagate: bool = True) -> Optional[str]:
        options = FILLET_UNIFORM_RADIUS | (FILLET_PROPAGATE if propagate else 0)

        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.FeatureFillet3(
                options, radius * MM, 0, 0, 0, 0, 0,
                (), (), (), (), (), (), (),
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def chamfer(
        self, width: float, angle_deg: float = 45.0, equal_distance: bool = True
    ) -> Optional[str]:
        ctype = CHAMFER_EQUAL_DISTANCE if equal_distance else CHAMFER_ANGLE_DISTANCE

        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.InsertFeatureChamfer(
                4, ctype, width * MM, math.radians(angle_deg), 0, 0, 0, 0
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def shell(self, thickness: float, outward: bool = False) -> None:
        def _do():
            doc = self._doc()
            doc.FeatureManager.InsertFeatureShell(thickness * MM, outward)

        self._worker.call(_do)

    def linear_pattern(
        self,
        count1: int,
        spacing1: float,
        count2: int = 1,
        spacing2: float = 0.0,
        flip1: bool = False,
        flip2: bool = False,
    ) -> Optional[str]:
        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.FeatureLinearPattern4(
                count1, spacing1 * MM, count2, spacing2 * MM,
                flip1, flip2, "", "", True, False,
                False, False, True, True, False, False, False, False, 0, 0,
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def circular_pattern(
        self, count: int, angle_deg: float = 360.0, axis_name: Optional[str] = None
    ) -> Optional[str]:
        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.FeatureCircularPattern5(
                count, math.radians(angle_deg), False, axis_name or "", False, True,
                False, False, False, False, 1, 0, "", True,
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def mirror(self, geometry_pattern: bool = True, merge: bool = False) -> Optional[str]:
        def _do():
            doc = self._doc()
            feat = doc.FeatureManager.InsertMirrorFeature2(
                False, geometry_pattern, merge, False, 0
            )
            return _name_of(feat)

        return self._worker.call(_do)

    def hole_wizard(
        self,
        diameter: float,
        depth: Optional[float] = None,
        standard_index: int = 1,
        fastener_type: int = 0,
        end_type: int = 0,
    ) -> Optional[str]:
        def _do():
            doc = self._doc()
            dep = (depth * MM) if depth is not None else 0.0
            feat = doc.FeatureManager.HoleWizard(
                0, standard_index, fastener_type, "", end_type, diameter * MM, dep,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            )
            return _name_of(feat)

        return self._worker.call(_do)

    # -- rebuild / inspection ----------------------------------------------
    def rebuild(self) -> None:
        """Force a full model rebuild (Ctrl-Q equivalent)."""
        def _do():
            rb = self._doc().EditRebuild3
            if callable(rb):
                rb()

        self._worker.call(_do)

    def mass_properties(self, density_kg_m3: float = 1000.0) -> dict:
        """Return volume/area/mass/centre-of-mass for the first solid body."""
        def _do():
            doc = self._doc()
            bodies = doc.GetBodies2(0, True)
            if not bodies:
                return {"bodies": 0}
            mp = list(bodies[0].GetMassProperties(density_kg_m3))
            return {
                "bodies": len(bodies),
                "center_of_mass_mm": [mp[0] * 1000.0, mp[1] * 1000.0, mp[2] * 1000.0],
                "volume_mm3": mp[3] * 1e9,
                "surface_area_mm2": mp[4] * 1e6,
                "mass_kg": mp[5],
            }

        return self._worker.call(_do)
