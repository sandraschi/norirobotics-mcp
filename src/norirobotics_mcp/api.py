"""FastAPI: REST dashboard + mounted MCP streamable HTTP."""

from __future__ import annotations

import os
import time
from collections import deque
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from norirobotics_mcp import session_state
from norirobotics_mcp.config import load_settings
from norirobotics_mcp.knowledge import FLEET_PEERS, NORI_HERO
from norirobotics_mcp.lifecycle import combined_lifespan
from norirobotics_mcp.robot_profiles import profile_store
from norirobotics_mcp.server import mcp
from norirobotics_mcp.tool_control import nori_control
from norirobotics_mcp.tool_recording import nori_recording
from norirobotics_mcp.tool_session import nori_session
from norirobotics_mcp.tools_manifest import MCP_TOOLS

mcp_http = mcp.http_app(path="/")
router = APIRouter(prefix="/api")
llm_router = APIRouter(prefix="/api/llm")

_start_time = time.time()
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_NORI_A3_GLB = _REPO_ROOT / "models" / "nori_description" / "nori_a3_posed.glb"
_NORI_A3_RIG_GLB = _REPO_ROOT / "models" / "nori_description" / "nori_a3_rig.glb"


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


@router.get("/status")
async def status() -> dict[str, Any]:
    """Richer status probe — uptime, tool count, session state (fleet 1E)."""
    return {
        "status": "ok",
        "service": "norirobotics-mcp",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "tool_count": len(MCP_TOOLS),
        "session_connected": session_state.get_session() is not None,
        "mock": session_state.is_mock(),
    }


@router.get("/capabilities")
async def capabilities() -> dict[str, Any]:
    """Standard capability shape for frontend discovery (fleet 1B/1E)."""
    return {
        "service": "norirobotics-mcp",
        "version": "0.1.0",
        "mcp_http_path": "/mcp",
        "tools": [t["name"] for t in MCP_TOOLS],
        "ports": {"backend": 11970, "frontend": 11971},
        "features": {"chat": True, "skills": False, "streaming": False},
    }


@router.get("/model/nori_a3.glb")
async def model_nori_a3() -> FileResponse:
    if not _NORI_A3_GLB.is_file():
        raise HTTPException(status_code=404, detail="nori_a3_posed.glb not found — run scripts/export_posed_mesh.py")
    return FileResponse(_NORI_A3_GLB, media_type="model/gltf-binary")


@router.get("/model/nori_a3_rig.glb")
async def model_nori_a3_rig() -> FileResponse:
    if not _NORI_A3_RIG_GLB.is_file():
        raise HTTPException(status_code=404, detail="nori_a3_rig.glb not found — run scripts/export_posed_mesh.py")
    return FileResponse(_NORI_A3_RIG_GLB, media_type="model/gltf-binary")


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


# ── Robot profiles (physical vs. virtual, multi-bot registry) ──────────


@router.get("/robot-profiles")
async def robot_profiles_list() -> dict[str, Any]:
    return {
        "profiles": [p.model_dump() for p in profile_store.list()],
        "active_id": profile_store.active_id(),
    }


@router.get("/robot-profiles/active")
async def robot_profiles_active() -> dict[str, Any]:
    """Lightweight endpoint for the AppLayout header badge — avoids fetching every
    saved profile just to show which one is currently active."""
    active = profile_store.get(profile_store.active_id())
    return {"active": active.model_dump() if active else None}


@router.post("/robot-profiles")
async def robot_profiles_add(body: dict[str, Any]) -> dict[str, Any]:
    result = await nori_session(
        operation="add_profile",
        profile_id=body.get("id"),
        name=body.get("name"),
        kind=body.get("kind"),
        supabase_url=body.get("supabase_url"),
        supabase_anon_key=body.get("supabase_anon_key"),
        robot_room=body.get("robot_room"),
        user_email=body.get("user_email"),
        user_password=body.get("user_password"),
    )
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error", "Could not add profile."))
    return result


@router.post("/robot-profiles/{profile_id}/activate")
async def robot_profiles_activate(profile_id: str) -> dict[str, Any]:
    result = await nori_session(operation="switch_profile", profile_id=profile_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Profile not found."))
    return result


@router.delete("/robot-profiles/{profile_id}")
async def robot_profiles_delete(profile_id: str) -> dict[str, Any]:
    result = await nori_session(operation="remove_profile", profile_id=profile_id)
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("error", "Could not remove profile."))
    return result


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


@router.post("/chat")
async def chat(body: dict[str, Any]) -> dict[str, Any]:
    """Fleet-standard chat alias (1E) — same non-streaming helper as /api/llm/chat."""
    return await llm_chat(body)


@router.post("/chat/stream")
async def chat_stream(body: dict[str, Any]) -> dict[str, Any]:
    """Fleet-standard stream alias (1E) — honestly non-streaming for now.

    Returns the full completion in one JSON payload with `"stream": False`
    so Chat clients can wire to the standard route today; true NDJSON
    streaming is a future enhancement, not silently faked.
    """
    result = await llm_chat(body)
    result["stream"] = False
    return result


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
