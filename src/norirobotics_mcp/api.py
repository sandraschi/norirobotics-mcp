"""FastAPI: REST dashboard + mounted MCP streamable HTTP."""

from __future__ import annotations

import os
import time
from collections import deque
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from norirobotics_mcp import session_state
from norirobotics_mcp.config import load_settings
from norirobotics_mcp.knowledge import FLEET_PEERS, NORI_HERO
from norirobotics_mcp.lifecycle import combined_lifespan
from norirobotics_mcp.server import mcp
from norirobotics_mcp.tool_control import nori_control
from norirobotics_mcp.tool_recording import nori_recording
from norirobotics_mcp.tool_session import nori_session
from norirobotics_mcp.tools_manifest import MCP_TOOLS

mcp_http = mcp.http_app(path="/")
router = APIRouter(prefix="/api")
llm_router = APIRouter(prefix="/api/llm")

_start_time = time.time()


# ── Ring-buffer activity log ──────────────────────────────────────────


class ActivityLog:
    def __init__(self, max_entries: int = 2000):
        self.max_entries = max_entries
        self._entries: deque[dict[str, Any]] = deque(maxlen=max_entries)

    def add(self, level: str, kind: str, detail: str, meta: dict | None = None) -> str:
        entry_id = f"{time.time():.6f}.{uuid4().hex[:6]}"
        self._entries.append(
            {
                "id": entry_id,
                "level": level.upper(),
                "kind": kind,
                "detail": detail,
                "meta": meta or {},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            }
        )
        return entry_id

    def query(self, limit=50, offset=0, level=None, search=None) -> dict:
        entries = list(self._entries)
        if level:
            entries = [e for e in entries if e["level"] == level.upper()]
        if search:
            q = search.lower()
            entries = [e for e in entries if q in e["detail"].lower()]
        entries.sort(key=lambda e: e["id"], reverse=True)
        return {"entries": entries[offset : offset + limit], "total": len(entries), "limit": limit, "offset": offset}

    def clear(self) -> None:
        self._entries.clear()


activity_log = ActivityLog()
log_router = APIRouter(prefix="/api/logs")


@log_router.get("")
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    level: str | None = Query(None),
    search: str | None = Query(None),
) -> dict[str, Any]:
    return activity_log.query(limit=limit, offset=offset, level=level, search=search)


@log_router.delete("")
async def clear_logs() -> dict[str, Any]:
    activity_log.clear()
    return {"success": True, "message": "Logs cleared."}


# ── Core REST ──────────────────────────────────────────────────────────


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "norirobotics-mcp"}


@router.get("/hero")
async def hero() -> dict[str, Any]:
    return {"hero": NORI_HERO, "fleet_peers": FLEET_PEERS}


@router.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools": MCP_TOOLS, "mcp_http_path": "/mcp"}


@router.get("/skills")
async def skills() -> dict[str, Any]:
    return {"skills": []}


@router.get("/session")
async def session_status() -> dict[str, Any]:
    return await nori_session(operation="status")


@router.post("/session/connect")
async def session_connect(force_mock: bool = Query(False)) -> dict[str, Any]:
    return await nori_session(operation="connect", force_mock=force_mock)


@router.post("/session/disconnect")
async def session_disconnect() -> dict[str, Any]:
    return await nori_session(operation="disconnect")


@router.post("/control/estop")
async def control_estop() -> dict[str, Any]:
    return await nori_control(operation="estop")


@router.post("/control/action")
async def control_action(body: dict[str, Any]) -> dict[str, Any]:
    return await nori_control(operation="action", targets=body.get("targets", {}), wait=body.get("wait", True))


@router.post("/recording/episode_start")
async def recording_episode_start(body: dict[str, Any]) -> dict[str, Any]:
    return await nori_recording(operation="episode_start", task=body.get("task"))


@router.post("/recording/episode_stop")
async def recording_episode_stop() -> dict[str, Any]:
    return await nori_recording(operation="episode_stop")


@llm_router.get("/providers")
async def llm_providers() -> dict[str, Any]:
    providers: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=3) as c:
        try:
            r = await c.get("http://127.0.0.1:11434/api/tags")
            if r.status_code == 200:
                providers["ollama"] = {
                    "url": "http://127.0.0.1:11434",
                    "models": [m["name"] for m in r.json().get("models", [])],
                }
        except Exception:
            pass
        try:
            r = await c.get("http://127.0.0.1:1234/v1/models")
            if r.status_code == 200:
                providers["lm_studio"] = {
                    "url": "http://127.0.0.1:1234",
                    "models": [m["id"] for m in r.json().get("data", [])],
                }
        except Exception:
            pass
    return {"providers": providers}


@llm_router.post("/chat")
async def llm_chat(body: dict[str, Any]) -> dict[str, Any]:
    provider = body.get("provider", "ollama")
    base_urls = {"ollama": "http://127.0.0.1:11434", "lm_studio": "http://127.0.0.1:1234"}
    base = base_urls.get(provider)
    if not base:
        return {"error": f"Unknown provider: {provider}"}
    payload = {"model": body.get("model", ""), "messages": body.get("messages", []), "stream": False}
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{base}/v1/chat/completions", json=payload)
            return r.json()
    except Exception as e:
        return {"error": str(e)}


def build_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="norirobotics-mcp", version="0.1.0", lifespan=combined_lifespan(mcp_http.lifespan))

    _tauri = os.environ.get("NORI_MCP_TAURI", "").lower() in ("1", "true", "yes")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:11970",
            "http://localhost:11970",
            "http://127.0.0.1:11971",
            "http://localhost:11971",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=(
            r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|"
            r"localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(llm_router)
    app.include_router(log_router)
    app.mount("/mcp", mcp_http)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "service": "norirobotics-mcp",
            "version": "0.1.0",
            "mcp_http": f"http://{settings.host}:{settings.port}/mcp",
            "api": f"http://{settings.host}:{settings.port}/api",
            "webapp": "http://127.0.0.1:11971",
            "mock": session_state.is_mock(),
        }

    return app


app = build_app()
