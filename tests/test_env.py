"""Environment self-check for the SolidWorks MCP project.

Verifies that the venv has the required runtime dependencies importable:
- pywin32 (win32com.client + pythoncom) for SolidWorks COM automation
- mcp (Model Context Protocol SDK) for the server transport
"""

import unittest


class TestRuntimeImports(unittest.TestCase):
    def test_pywin32_importable(self):
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401

    def test_pywin32_version_reported(self):
        import win32api

        ver = win32api.GetFileVersionInfo(
            win32api.GetModuleFileName(0), "\\"
        )
        self.assertIn("FileVersionMS", ver)

    def test_mcp_importable(self):
        import mcp  # noqa: F401


if __name__ == "__main__":
    unittest.main()
