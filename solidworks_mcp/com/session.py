"""High-level session wrapper around a SolidWorks COM instance.

All methods funnel their actual COM work through :class:`ComWorker` so every
call runs on the single STA thread. Business methods here stay synchronous and
raise ordinary Python exceptions on failure.
"""

from __future__ import annotations

import os
from typing import Optional

import pythoncom
import win32com.client
from win32com.client import VARIANT

from .. import config
from . import gencache_bootstrap
from .worker import ComWorker

# swUserPreferenceStringValue_e: default document templates.
SW_DEFAULT_TEMPLATE_ASSEMBLY = 7
SW_DEFAULT_TEMPLATE_PART = 8
SW_DEFAULT_TEMPLATE_DRAWING = 9

# swDocumentTypes_e
SW_DOC_PART = 1
SW_DOC_ASSEMBLY = 2
SW_DOC_DRAWING = 3

# swSaveAsOptions_e
SW_SAVE_AS_SILENT = 1

_TEMPLATE_CONST = {
    "part": SW_DEFAULT_TEMPLATE_PART,
    "assembly": SW_DEFAULT_TEMPLATE_ASSEMBLY,
    "drawing": SW_DEFAULT_TEMPLATE_DRAWING,
}

_TEMPLATE_EXT = {
    "part": ".prtdot",
    "assembly": ".asmdot",
    "drawing": ".drwdot",
}

_DOC_TYPE_OF_TEMPLATE = {
    "part": SW_DOC_PART,
    "assembly": SW_DOC_ASSEMBLY,
    "drawing": SW_DOC_DRAWING,
}


def _get_title(doc) -> str:
    """GetTitle is exposed as a property by pywin32; tolerate either form."""
    value = doc.GetTitle
    return value() if callable(value) else str(value)


def _get_path(doc) -> str:
    value = doc.GetPathName
    return value() if callable(value) else str(value)


def _byref_int() -> VARIANT:
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def _null_dispatch() -> VARIANT:
    return VARIANT(pythoncom.VT_DISPATCH, None)


class SolidWorksSession:
    """Connect to SolidWorks and manage documents on one STA thread."""

    def __init__(self, worker: ComWorker, visible: bool = True) -> None:
        self._worker = worker
        self._visible = visible
        self._sw = None
        self._template_cache: dict[str, str] = {}

    # -- connection ---------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._sw is not None

    @property
    def worker(self) -> ComWorker:
        return self._worker

    def require_sw(self):
        """Return the connected ISldWorks object (raises if not connected)."""
        return self._require_sw()

    def _require_sw(self):
        if self._sw is None:
            raise RuntimeError("Not connected to SolidWorks; call sw_connect first.")
        return self._sw

    def connect(self) -> str:
        """Attach to a running SolidWorks instance, launching one if needed."""
        if self._sw is None:
            # Materialize the early-binding cache so vtable-only members
            # (e.g. ActiveDoc) are available; fall back to late binding otherwise.
            try:
                gencache_bootstrap.ensure_solidworks_module()
            except Exception:  # noqa: BLE001 - late binding still covers basics
                pass

            def _do():
                sw = win32com.client.Dispatch("SldWorks.Application")
                try:
                    sw.Visible = self._visible
                except Exception:  # noqa: BLE001 - visibility is best-effort
                    pass
                return sw

            self._sw = self._worker.call(_do)
        return self.revision()

    def revision(self) -> str:
        sw = self._require_sw()

        def _do():
            rev = sw.RevisionNumber
            return rev() if callable(rev) else str(rev)

        return self._worker.call(_do)

    # -- templates ----------------------------------------------------------

    def resolve_template(self, kind: str) -> str:
        """Return the template path for 'part' | 'assembly' | 'drawing'."""
        if kind not in _TEMPLATE_CONST:
            raise ValueError(f"Unknown template kind: {kind!r}")
        if kind in self._template_cache:
            return self._template_cache[kind]
        sw = self._require_sw()
        const = _TEMPLATE_CONST[kind]

        def _do():
            try:
                return sw.GetUserPreferenceStringValue(const) or ""
            except Exception:  # noqa: BLE001 - fall back to known path
                return ""

        pref = self._worker.call(_do)
        ext = _TEMPLATE_EXT[kind]
        path = (
            pref
            if pref and pref.lower().endswith(ext) and os.path.exists(pref)
            else config.template_path(kind)
        )
        if not os.path.exists(path):
            raise FileNotFoundError(f"No {kind} template found (tried {path!r}).")
        self._template_cache[kind] = path
        return path

    # -- documents ----------------------------------------------------------

    def new_document(self, kind: str = "part", template: Optional[str] = None) -> str:
        tmpl = template or self.resolve_template(kind)
        sw = self._require_sw()

        def _do():
            doc = sw.NewDocument(tmpl, 0, 0, 0)
            if doc is None:
                raise RuntimeError(f"NewDocument returned None for template {tmpl!r}.")
            return _get_title(doc)

        return self._worker.call(_do)

    def open_document(self, path: str, kind: str = "part") -> str:
        sw = self._require_sw()
        abs_path = os.path.abspath(path)
        doc_type = _DOC_TYPE_OF_TEMPLATE[kind]

        def _do():
            errs = _byref_int()
            warns = _byref_int()
            doc = sw.OpenDoc6(abs_path, doc_type, 0, "", errs, warns)
            if doc is None:
                raise RuntimeError(
                    f"Failed to open {abs_path!r} (error={errs.value}, warning={warns.value})."
                )
            return _get_title(doc)

        return self._worker.call(_do)

    def active_title(self) -> Optional[str]:
        sw = self._require_sw()

        def _do():
            doc = sw.ActiveDoc
            return None if doc is None else _get_title(doc)

        return self._worker.call(_do)

    def list_open_documents(self) -> list[str]:
        sw = self._require_sw()

        def _do():
            docs = sw.GetDocuments
            if callable(docs):
                docs = docs()
            return [_get_title(doc) for doc in (docs or ())]

        return self._worker.call(_do)

    def save_as(self, path: str) -> str:
        sw = self._require_sw()
        abs_path = os.path.abspath(path)

        def _do():
            doc = sw.ActiveDoc
            if doc is None:
                raise RuntimeError("No active document to save.")
            result = doc.SaveAs3(abs_path, 0, SW_SAVE_AS_SILENT)
            if result != 0:
                raise RuntimeError(f"SaveAs3 failed for {abs_path!r} (code={result}).")
            return abs_path

        return self._worker.call(_do)

    def save(self, path: Optional[str] = None) -> str:
        """Save the active document, or SaveAs when a path is given."""
        if path:
            return self.save_as(path)
        sw = self._require_sw()

        def _do():
            doc = sw.ActiveDoc
            if doc is None:
                raise RuntimeError("No active document to save.")
            errs = _byref_int()
            warns = _byref_int()
            ok = doc.Save3(SW_SAVE_AS_SILENT, errs, warns)
            if not ok:
                raise RuntimeError(
                    f"Save3 failed (error={errs.value}, warning={warns.value})."
                )
            return _get_path(doc)

        return self._worker.call(_do)

    def save_screenshot(self, path: str, width: int = 1280, height: int = 960) -> str:
        """Save a bitmap snapshot of the active document for visual feedback."""
        sw = self._require_sw()
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        def _do():
            doc = sw.ActiveDoc
            if doc is None:
                raise RuntimeError("No active document to capture.")
            doc.SaveBMP(abs_path, width, height)
            return abs_path

        return self._worker.call(_do)

    def close(self, title: Optional[str] = None) -> bool:
        """Close a document by title, or the active one when title is None."""
        sw = self._require_sw()

        def _do():
            docs = sw.GetDocuments
            if callable(docs):
                docs = docs()
            docs = list(docs or ())
            if title is None:
                doc = sw.ActiveDoc
                if doc is None:
                    return False
                name = _get_title(doc)
            else:
                name = title
                doc = next((d for d in docs if _get_title(d) == title), None)
                if doc is None:
                    return False
            # Discard unsaved changes so CloseDoc does not raise a save prompt.
            try:
                doc.SetSaveFlag()
            except Exception:  # noqa: BLE001 - best effort
                pass
            sw.CloseDoc(name)
            # CloseDoc is void under early binding; verify by re-reading the list.
            remaining = sw.GetDocuments
            if callable(remaining):
                remaining = remaining()
            return name not in [_get_title(d) for d in (remaining or ())]

        return self._worker.call(_do)
