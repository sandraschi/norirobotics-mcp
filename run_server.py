"""Entry point for PyInstaller-bundled norirobotics-mcp HTTP backend.

norirobotics_mcp.__main__.main() uses argparse and reads a --serve flag to
switch into HTTP mode (host/port come from load_settings(), env_prefix
"NORI_MCP_" — not from CLI flags). PyInstaller leaves the frozen process's
original argv in place, so sys.argv must be overwritten BEFORE main() parses
it, or argparse will choke on/ignore the real invocation args.
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "src")

sys.argv = ["run_server.py", "--serve"]

from norirobotics_mcp.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main() or 0)
