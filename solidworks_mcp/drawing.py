"""Drawing (2D) automation: sheets, views, model annotations, export."""

from __future__ import annotations

import os
from typing import Optional

import pythoncom
from win32com.client import VARIANT

from .com.session import SolidWorksSession

# swInsertAnnotations_e: model dimensions.
ANN_DIMENSIONS = 2
# swInsertDimensions_e: all dimension types.
DIM_ALL_TYPES = 0x3F

VIEW_NAMES = {
    "front": "*前视",
    "back": "*后视",
    "top": "*上视",
    "bottom": "*下视",
    "left": "*左视",
    "right": "*右视",
    "isometric": "*等轴测",
    "trimetric": "*上下二等角轴测",
    "dimetric": "*左右二等角轴测",
}

# English fallbacks, tried when the localized name does not resolve.
VIEW_NAME_FALLBACKS = {
    "front": "*Front",
    "back": "*Back",
    "top": "*Top",
    "bottom": "*Bottom",
    "left": "*Left",
    "right": "*Right",
    "isometric": "*Isometric",
    "trimetric": "*Trimetric",
    "dimetric": "*Dimetric",
}


def _byref_int() -> VARIANT:
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def _null_dispatch() -> VARIANT:
    return VARIANT(pythoncom.VT_DISPATCH, None)


class Drawing:
    def __init__(self, session: SolidWorksSession) -> None:
        self._session = session
        self._worker = session.worker

    def _doc(self):
        doc = self._session.require_sw().ActiveDoc
        if doc is None:
            raise RuntimeError("No active drawing document.")
        return doc

    def new_drawing(self, template: Optional[str] = None) -> str:
        return self._session.new_document("drawing", template)

    def create_view(
        self, model_path: str, view: str = "front", x: float = 0.0, y: float = 0.0
    ) -> Optional[str]:
        """Insert a model view (front|top|right|left|back|bottom|isometric|...).

        Coordinates are metres on the sheet.
        """
        vname = VIEW_NAMES.get(view, view)
        fallback = VIEW_NAME_FALLBACKS.get(view)
        candidates = [vname] + ([fallback] if fallback and fallback != vname else [])
        abs_path = os.path.abspath(model_path)

        def _do():
            doc = self._doc()
            for cand in candidates:
                v = doc.CreateDrawViewFromModelView3(abs_path, cand, x, y, 0.0)
                if v is not None:
                    return v.Name
            return None

        return self._worker.call(_do)

    def insert_model_annotations(self, all_views: bool = True) -> None:
        """Insert the model's dimensions/annotations onto the drawing views."""

        def _do():
            self._doc().InsertModelAnnotations3(
                ANN_DIMENSIONS, DIM_ALL_TYPES, all_views, False, False, False
            )

        self._worker.call(_do)

    def export(self, path: str) -> str:
        """Export the drawing by file extension (e.g. .pdf or .dwg)."""
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        def _do():
            doc = self._doc()
            errs = _byref_int()
            warns = _byref_int()
            ok = doc.Extension.SaveAs(abs_path, 0, 0, _null_dispatch(), errs, warns)
            if not ok:
                raise RuntimeError(
                    f"Export failed for {abs_path!r} "
                    f"(error={errs.value}, warning={warns.value})."
                )
            return abs_path

        return self._worker.call(_do)
