"""Regenerate the SolidWorks early-binding cache into the project directory.

Usage (from the project root, with the venv):

    .venv\\Scripts\\python.exe scripts\\build_gencache.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solidworks_mcp.com import gencache_bootstrap  # noqa: E402


def main() -> int:
    path = gencache_bootstrap.configure()
    print(f"gen_py dir: {path}", flush=True)
    module = gencache_bootstrap.ensure_solidworks_module()
    print(f"module: {module}", flush=True)

    # Confirm early binding now exposes vtable-only members.
    import win32com.client

    sw = win32com.client.Dispatch("SldWorks.Application")
    sw.Visible = True
    print(f"ActiveDoc: {sw.ActiveDoc}", flush=True)
    print(f"GetFirstDocument: {sw.GetFirstDocument()}", flush=True)
    print(f"GetDocuments: {sw.GetDocuments()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
