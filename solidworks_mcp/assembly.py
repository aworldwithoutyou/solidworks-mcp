"""Assembly automation: components, mates, interference, exploded views."""

from __future__ import annotations

import os
from typing import Optional

import pythoncom
from win32com.client import VARIANT

from .com.session import SolidWorksSession

MM = 0.001

# swMateType_e
MATE_COINCIDENT = 0
MATE_CONCENTRIC = 1
MATE_PERPENDICULAR = 2
MATE_PARALLEL = 3
MATE_TANGENT = 4
MATE_DISTANCE = 5
MATE_ANGLE = 6

# swMateAlign_e
ALIGN_SAME = 0
ALIGN_OPPOSITE = 1
ALIGN_CLOSEST = 2


def _byref_int() -> VARIANT:
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def _null_dispatch() -> VARIANT:
    return VARIANT(pythoncom.VT_DISPATCH, None)


def _byref_dispatch() -> VARIANT:
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_DISPATCH, None)


class Assembly:
    def __init__(self, session: SolidWorksSession) -> None:
        self._session = session
        self._worker = session.worker

    def _doc(self):
        doc = self._session.require_sw().ActiveDoc
        if doc is None:
            raise RuntimeError("No active assembly document.")
        return doc

    def new_assembly(self, template: Optional[str] = None) -> str:
        return self._session.new_document("assembly", template)

    def add_component(
        self, path: str, x: float = 0.0, y: float = 0.0, z: float = 0.0
    ) -> Optional[str]:
        def _do():
            comp = self._doc().AddComponent4(
                os.path.abspath(path), "", x * MM, y * MM, z * MM
            )
            return comp.Name if comp is not None else None

        return self._worker.call(_do)

    def select_at(
        self, x: float, y: float, z: float, type_: str = "FACE", append: bool = True
    ) -> bool:
        def _do():
            doc = self._doc()
            return bool(
                doc.Extension.SelectByID2(
                    "", type_, x * MM, y * MM, z * MM, append, 0, _null_dispatch(), 0
                )
            )

        return self._worker.call(_do)

    def select_component(self, name: str, append: bool = False) -> bool:
        """Select a component by its instance name (e.g. 'b-1')."""
        def _do():
            doc = self._doc()
            return bool(
                doc.Extension.SelectByID2(
                    name, "COMPONENT", 0, 0, 0, append, 0, _null_dispatch(), 0
                )
            )

        return self._worker.call(_do)

    def clear_selection(self) -> None:
        def _do():
            self._doc().ClearSelection2(True)

        self._worker.call(_do)

    def add_mate(
        self,
        mate_type: int = MATE_COINCIDENT,
        align: int = ALIGN_CLOSEST,
        distance: float = 0.0,
        angle: float = 0.0,
    ) -> dict:
        """Add a mate between the two currently selected entities."""
        def _do():
            errs = _byref_int()
            mate = self._doc().AddMate3(
                mate_type, align, False, distance * MM, 0, 0, 0, 0,
                angle, 0, 0, False, errs,
            )
            return {
                "mate": (mate.Name if mate is not None else None),
                "error": errs.value,
            }

        return self._worker.call(_do)

    def interference_check(self, coincident: bool = True) -> dict:
        def _do():
            doc = self._doc()
            comps = doc.GetComponents(False)
            comps = list(comps) if comps is not None else []
            if not comps:
                return {"interferences": 0}
            doc.ToolsCheckInterference2(
                len(comps), comps, coincident, _byref_dispatch(), _byref_dispatch()
            )
            return {"interferences": int(doc.GetInterferenceCount())}

        return self._worker.call(_do)

    def create_exploded_view(self) -> bool:
        def _do():
            ev = self._doc().CreateExplodedView
            return ev() if callable(ev) else bool(ev)

        return self._worker.call(_do)

    def add_explode_step(self, distance: float, reverse: bool = False) -> bool:
        """Add an explode step for the selected component(s)."""
        def _do():
            self._doc().AddExplodeStep(distance * MM, reverse, False, False)
            return True

        return self._worker.call(_do)
