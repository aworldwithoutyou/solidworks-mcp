"""Batch parameter editing and multi-format export.

Parameter values cross this API boundary in millimetres; SolidWorks stores
them in metres (``Dimension.SystemValue``).
"""

from __future__ import annotations

import os

import pythoncom
from win32com.client import VARIANT

from .com.session import SolidWorksSession

MM = 0.001


def _byref_int() -> VARIANT:
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def _null_dispatch() -> VARIANT:
    return VARIANT(pythoncom.VT_DISPATCH, None)


class Batch:
    def __init__(self, session: SolidWorksSession) -> None:
        self._session = session
        self._worker = session.worker

    def _doc(self):
        doc = self._session.require_sw().ActiveDoc
        if doc is None:
            raise RuntimeError("No active document.")
        return doc

    def get_parameter(self, name: str):
        """Read a named dimension's value in mm (e.g. 'D1@凸台-拉伸1')."""
        def _do():
            p = self._doc().Parameter(name)
            return p.SystemValue / MM if p is not None else None

        return self._worker.call(_do)

    def set_parameter(self, name: str, value_mm: float) -> float:
        """Set a named dimension (mm) and rebuild. Returns the new value in mm."""
        def _do():
            doc = self._doc()
            p = doc.Parameter(name)
            if p is None:
                raise RuntimeError(f"Parameter {name!r} not found.")
            p.SystemValue = value_mm * MM
            rb = doc.EditRebuild3
            if callable(rb):
                rb()
            return p.SystemValue / MM

        return self._worker.call(_do)

    def export(self, path: str) -> str:
        """Export the active document by extension (STEP/DXF/PDF/...)."""
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
