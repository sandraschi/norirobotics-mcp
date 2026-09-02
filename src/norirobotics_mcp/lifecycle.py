"""FastAPI lifespan: MCP HTTP app only. Nori sessions are opened on-demand (nori_session tool),
not eagerly at server startup — there's no bridge to eagerly connect to, and Supabase
credentials being absent is the expected default state pre-hardware."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from norirobotics_mcp import session_state

logger = logging.getLogger("norirobotics-mcp.lifecycle")


def combined_lifespan(mcp_lifespan):
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        async with mcp_lifespan(app):
            try:
                yield
            finally:
                logger.info("Shutting down — closing any open Nori session")
                await session_state.disconnect()

    return _lifespan
