"""Entry point for PyInstaller-bundled norirobotics-mcp HTTP backend.

norirobotics_mcp.__main__.main() uses argparse and reads --serve flag to
switch into HTTP mode (host/port come from load_settings(), env_prefix
"NORI_MCP_" — not from CLI flags). PyInstaller leaves the frozen process's
original argv in place, so sys.argv must be overwritten BEFORE main() parses
it, or argparse will choke on/ignore the real invocation args.

Eager imports of _strptime/_datetime/mcp.types/joserfc are required for
frozen builds — PyInstaller's static analysis misses them.
"""

# Eager stdlib C extensions — hiddenimports alone failed in plex-mcp
import _datetime  # noqa: F401
import _strptime  # noqa: F401
import sys
from pathlib import Path

# Eager mcp/fastmcp bootstrap — before any tool code
import mcp.types  # noqa: F401

try:
    import joserfc
    import joserfc.jwk
    import joserfc.jwt  # noqa: F401
except ImportError:
    pass

# Path setup — frozen vs dev
if getattr(sys, "frozen", False):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    sys.path.insert(0, str(base))
    # datas are collected as ("src/norirobotics_mcp", "norirobotics_mcp")
    if (base / "norirobotics_mcp").exists():
        sys.path.insert(0, str(base))
else:
    sys.path.insert(0, ".")
    sys.path.insert(0, "src")

# Frozen argv handling — env vars already handled via load_settings, but ensure --serve
sys.argv = ["run_server.py", "--serve"]

from norirobotics_mcp.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main() or 0)
