"""Close all documents currently open in SolidWorks, discarding changes.

Usage (from the project root, with the venv):

    .venv\\Scripts\\python.exe scripts\\cleanup_sw.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pythoncom  # noqa: E402
import win32com.client  # noqa: E402

from solidworks_mcp.com import gencache_bootstrap  # noqa: E402


def main() -> int:
    gencache_bootstrap.ensure_solidworks_module()
    pythoncom.CoInitialize()
    try:
        sw = win32com.client.Dispatch("SldWorks.Application")
        docs = sw.GetDocuments
        if callable(docs):
            docs = docs()
        titles = [d.GetTitle for d in (docs or ())]
        print(f"open documents before: {titles}", flush=True)
        for title in titles:
            sw.CloseDoc(title)
        docs = sw.GetDocuments
        if callable(docs):
            docs = docs()
        print(
            f"open documents after: {[d.GetTitle for d in (docs or ())]}",
            flush=True,
        )
        return 0
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    sys.exit(main())
