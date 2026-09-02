"""CLI: stdio (Claude Desktop) or HTTP (FastAPI + /mcp + /api)."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

import uvicorn

from norirobotics_mcp.config import load_settings
from norirobotics_mcp.server import mcp


def _configure_logging(*, debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="norirobotics-mcp (FastMCP 3.4)")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run FastAPI on NORI_MCP_HOST:NORI_MCP_PORT with MCP at /mcp and REST at /api",
    )
    parser.add_argument("--stdio", action="store_true", help="MCP stdio only (default if --serve not passed)")
    parser.add_argument("--debug", action="store_true", help="Verbose stderr logs")
    args = parser.parse_args()
    _configure_logging(debug=args.debug)

    transport = os.getenv("MCP_TRANSPORT", "").lower()
    use_http = args.serve or transport in {"http", "streamable"}

    if use_http and args.stdio:
        parser.error("Choose either --serve or --stdio, not both.")

    if use_http:
        s = load_settings()
        uvicorn.run(
            "norirobotics_mcp.api:app",
            host=s.host,
            port=s.port,
            log_level="debug" if args.debug else "info",
        )
        return

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
