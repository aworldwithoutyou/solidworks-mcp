"""Verify the MCP server starts over stdio and lists its tools.

Launches ``python -m solidworks_mcp.server`` as a subprocess and performs the
MCP handshake (initialize -> notifications/initialized -> tools/list).

Usage (from the project root, with the venv):

    .venv\\Scripts\\python.exe scripts\\check_stdio.py
"""

import json
import os
import subprocess
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(PROJECT, ".venv", "Scripts", "python.exe")


def send(proc: subprocess.Popen, obj: dict) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def read_msg(proc: subprocess.Popen):
    assert proc.stdout is not None
    line = proc.stdout.readline()
    if not line:
        return None
    return json.loads(line)


def main() -> int:
    proc = subprocess.Popen(
        [PY, "-m", "solidworks_mcp.server"],
        cwd=PROJECT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    try:
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "check_stdio", "version": "1"},
                },
            },
        )
        init = read_msg(proc)
        print(f"initialize result: {init}", flush=True)

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = read_msg(proc)
        tools = [t["name"] for t in listed["result"]["tools"]]
        print(f"tools ({len(tools)}): {tools}", flush=True)
        return 0 if tools else 1
    finally:
        proc.terminate()
        try:
            err = proc.stderr.read() if proc.stderr else ""
        except Exception:  # noqa: BLE001
            err = ""
        if err:
            print(f"--- server stderr ---\n{err}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
