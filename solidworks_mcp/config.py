"""Central configuration: paths and constants, with env-var overrides.

Environment variables (all optional — runtime auto-detection is the fallback):

- ``SOLIDWORKS_TEMPLATES_DIR`` : directory holding the document templates
  (``*.prtdot`` / ``*.asmdot`` / ``*.drwdot``).
- ``SOLIDWORKS_INSTALL_DIR``   : SolidWorks install root (the directory that
  contains ``sldworks.tlb`` / ``SLDWORKS.exe``).
- ``SOLIDWORKS_MCP_GENPY``     : directory for the win32com early-binding cache.

Keeping these centralized means the project is portable: point the env vars at
a machine's actual locations instead of editing code.
"""

from __future__ import annotations

import glob
import os

# Preferred GB template file names (SolidWorks Chinese Simplified installs).
TEMPLATE_FILES = {
    "part": "gb_part.prtdot",
    "assembly": "gb_assembly.asmdot",
    "drawing": "gb_a3.drwdot",
}

TEMPLATE_EXT = {
    "part": ".prtdot",
    "assembly": ".asmdot",
    "drawing": ".drwdot",
}

_INSTALL_CANDIDATES = (
    r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS",
    r"D:\Program Files\SOLIDWORKS Corp\SOLIDWORKS",
    r"E:\Program Files\SOLIDWORKS Corp\SOLIDWORKS",
)


def install_dir() -> str:
    """SolidWorks install root (dir containing ``SLDWORKS.exe`` / ``sldworks.tlb``)."""
    env = os.environ.get("SOLIDWORKS_INSTALL_DIR")
    candidates = [env] + list(_INSTALL_CANDIDATES)
    for root in candidates:
        if not root:
            continue
        if os.path.isfile(os.path.join(root, "SLDWORKS.exe")) or os.path.isfile(
            os.path.join(root, "sldworks.tlb")
        ):
            return root
    return env or ""


def _template_dirs() -> list[str]:
    """Candidate template directories, in priority order."""
    dirs: list[str] = []
    env = os.environ.get("SOLIDWORKS_TEMPLATES_DIR")
    if env and os.path.isdir(env):
        dirs.append(env)
    for pd in (os.environ.get("PROGRAMDATA"), r"C:\ProgramData"):
        if not pd:
            continue
        dirs += sorted(
            glob.glob(os.path.join(pd, "SOLIDWORKS", "SOLIDWORKS *", "templates"))
        )
    root = install_dir()
    dirs += [
        os.path.join(root, "data", "templates"),
        os.path.join(root, "templates"),
    ]
    return dirs


def templates_dir() -> str:
    """Directory that actually holds part/assembly/drawing templates."""
    for d in _template_dirs():
        if not os.path.isdir(d):
            continue
        names = [n.lower() for n in os.listdir(d)]
        if any(n.endswith(".prtdot") for n in names):
            return d
    for d in _template_dirs():
        if os.path.isdir(d):
            return d
    return ""


def template_path(kind: str) -> str:
    """Path to a template file for 'part' | 'assembly' | 'drawing' ('' if none)."""
    if kind not in TEMPLATE_FILES:
        raise ValueError(f"Unknown template kind: {kind!r}")
    ext = TEMPLATE_EXT[kind]
    # Prefer the named GB template, then any file with the right extension.
    for d in _template_dirs():
        if not os.path.isdir(d):
            continue
        path = os.path.join(d, TEMPLATE_FILES[kind])
        if os.path.isfile(path):
            return path
    for d in _template_dirs():
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.lower().endswith(ext):
                return os.path.join(d, name)
    return ""


def genpy_dir() -> str:
    """Directory for the win32com early-binding cache."""
    return os.environ.get("SOLIDWORKS_MCP_GENPY") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gen_py"
    )
