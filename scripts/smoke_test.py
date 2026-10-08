"""COM smoke test for SolidWorks 2022.

Connects to a running (or launches a new) SolidWorks instance via COM,
reads the revision number, creates an empty part from the GB template,
then closes it. Prints each step so failures are localized.

Run with the project venv:
    .venv\\Scripts\\python.exe scripts\\smoke_test.py
"""

import sys
import traceback

import pythoncom
import win32com.client

from solidworks_mcp import config


def _revision(sw) -> str:
    """RevisionNumber is exposed as a property in pywin32; fall back to a call."""
    rev = getattr(sw, "RevisionNumber", None)
    if rev is None:
        return "<unknown>"
    return rev() if callable(rev) else rev


def main() -> int:
    pythoncom.CoInitialize()
    try:
        print("Dispatch SldWorks.Application ...", flush=True)
        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = True
        print(f"Connected. RevisionNumber={_revision(sw)}", flush=True)

        part_template = config.template_path("part")
        if not part_template:
            print("No part template found; set SOLIDWORKS_TEMPLATES_DIR.", flush=True)
            return 2
        print(f"NewDocument from {part_template} ...", flush=True)
        doc = sw.NewDocument(part_template, 0, 0, 0)
        if doc is None:
            print(
                "NewDocument returned None (a dialog may be waiting for input)",
                flush=True,
            )
            return 2
        got_title = doc.GetTitle
        title = got_title() if callable(got_title) else got_title
        print(f"Created document: {title}", flush=True)

        # Mark as saved so CloseDoc does not raise a save prompt.
        try:
            doc.SetSaveFlag()
        except Exception as exc:  # noqa: BLE001 - best effort, report and continue
            print(f"SetSaveFlag failed (continuing): {exc}", flush=True)

        sw.CloseDoc(title)
        print("Closed document OK", flush=True)
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    sys.exit(main())
