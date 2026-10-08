"""Pin win32com's generated COM cache to a stable, project-local directory.

win32com stores makepy-generated early-binding modules under ``%TEMP%\\gen_py``
by default, which this session's temp dir wipes on exit. We relocate the cache
under the project and expose a helper to materialize the SolidWorks 2022 type
library there, so the server always gets full (vtable) method coverage without
regenerating on every run.
"""

from __future__ import annotations

import os
import sys
import types

import win32com

from .. import config

GENPY_DIR = config.genpy_dir()

# SolidWorks type library identity, taken from sldworks.tlb (see makepy output
# filename ``{GUID}x0x30x0.py``).
SW_TLB_CLSID = "{83A33D31-27C5-11CE-BFD4-00400513BB57}"
SW_TLB_LCID = 0
SW_TLB_MAJOR = 30
SW_TLB_MINOR = 0


def configure() -> str:
    """Redirect the win32com generation path to the project and return it."""
    os.makedirs(GENPY_DIR, exist_ok=True)
    win32com.__gen_path__ = GENPY_DIR
    # win32com.gen_py is registered at import time against the old path; retarget it.
    gen_py = sys.modules.get("win32com.gen_py")
    if gen_py is None:
        gen_py = types.ModuleType("win32com.gen_py")
        sys.modules["win32com.gen_py"] = gen_py
    gen_py.__path__ = [GENPY_DIR]
    return GENPY_DIR


def ensure_solidworks_module():
    """Generate/import the SolidWorks early-binding module into GENPY_DIR.

    Returns the generated module, or None when the type library is unavailable
    (in which case callers fall back to late binding).
    """
    configure()
    from win32com.client import gencache

    return gencache.EnsureModule(
        SW_TLB_CLSID, SW_TLB_LCID, SW_TLB_MAJOR, SW_TLB_MINOR
    )
