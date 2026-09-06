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
from norirobotics_mcp.tool_vr import nori_vr
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
        "features": {"chat": True, "skills": True, "streaming": False, "vr": True},
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
    return {
        "skills": [
            {
                "name": "nori-a3-expert",
                "id": "nori-a3-expert",
                "description": "Nori A3 deep expert — 19-DOF wheeled bimanual home robot (ships Fall 2026). Specs, nori-sdk WebRTC/Supabase, session/actuator safety, LeRobot recording, live 3D rig, VR spawning via fleet, troubleshooting.",
                "content": (
                    "# Nori A3 Expert\n\n"
                    "You are the Nori A3 expert. Answer with specifics, cite SDK lineage, never invent a local serial API.\n\n"
                    "## What Nori A3 is\n"
                    "- 19-DOF wheeled bimanual: 2×7+1-DOF arms + 3-stage telescoping column (69–145cm, 76cm travel @30mm/s) + differential drive base\n"
                    "- 55cm reach, 1.5kg payload/arm, 4×720p 30fps cameras (grippers×2, head, neck), 2D LiDAR 12m, 432Wh 6–8h\n"
                    "- Actuators: Feetech STS-series bus servos (STS3095/3250/3215) torque-graded; soft TPU fingers, sensorless force from servo current; Pi 5 4GB does bus I/O only, no onboard inference\n"
                    "- Price $1,688, YC S26, ships Fall 2026, no deposit — no unit in this household yet, mock is `nori_sdk.mock_session()`\n"
                    "## SDK & transport\n"
                    "- `nori-sdk` (Apache-2.0) `RemoteTeleop` over **WebRTC data channel + Supabase Realtime signaling** — no serial/USB/ROS. Host/port from `NORI_MCP_*` env, not CLI.\n"
                    "- Session: `nori_session(connect)` → `wait_ready` → `nori_control`/`nori_recording` → `disconnect`. Profiles: Virtual Twin (always) + named physical A3s in `robot_profiles` store.\n"
                    "## Control & safety\n"
                    "- `nori_control`: motion `jog`/`set_jog`/`clear_jog`/`action`/`pose(side, position_m)` + safety `estop`/`estop_confirmed`/`reset_latch`/`reset_arm`. Every call maps 1:1 to `nori_sdk`; calibration clamping/stall/thermal is in-robot, not this repo.\n"
                    "- `nori_recording`: LeRobot-compatible episodes `episode_start(task)` / `episode_stop` / `snapshot` / `frames` / `set_bitrate` / `set_paused`.\n"
                    "## 3D & VR\n"
                    "- Live 3D rig from real glTF: `nori_a3_posed.glb` (73,974 verts) + `nori_a3_rig.glb`; viewer is Three.js `BotViewer` with orbit/wireframe/wave demo.\n"
                    '- Virtual twin via other fleet repos: `robotics-mcp` `robot_virtual`/`vbot_crud` (`platform="resonite"|"overte"|"unity"|"godot"`) pushes `scripts/export_posed_mesh.py` output (`nori_a3_posed.glb` + `nori_a3_posed.mesh.json` 26k tris) via `resonite-mcp`/`overte-mcp`/`godot-mcp`/`unity3d-mcp` (`unity_spawn` now real via model depot). MuJoCo local, Isaac USD via `isaac-mcp`.\n'
                    "## Lineage & community\n"
                    "- Prior XLeRobot base (SO-100/SO-101 + Lekiwi + IKEA cart, HF LeRobot); A3 is clean-sheet but carries lift/protection/force channel. HN launch: 97 pts/36 comments — praise price/wheeled safety/open SDK; criticism RC-servo vs QDD (CubeMars/MyActuator), staged-demo skepticism, WebRTC privacy.\n"
                    "## When to act\n"
                    "- No session needed for `nori_info`; session-gated for `nori_control`/`nori_recording`. Always `connect` first. Be precise, quote specs, link SDK.\n"
                ),
            },
            {
                "name": "homebot-expert",
                "id": "homebot-expert",
                "description": "Home robot generalist — wheeled vs legged, PRC vs US, DIY vs product, actuators, compute, safety, cost, VLA, fleet patterns.",
                "content": (
                    "# Homebot Expert\n\n"
                    "You are the home robot generalist. Cover wheeled vs legged, PRC vs US, DIY vs product, cheap vs capable.\n\n"
                    "## Morphology\n"
                    "- Wheeled (Nori A3, Dreame, etc.): cheap, safe, stable, 6–8h battery, needs flat floors; legged (Unitree H1/G1, etc.): stairs/uneven terrain, expensive, power-hungry, still research. Nori's bet: wheels + telescoping column + tiered grippers is the near-term home winner.\n"
                    "## Supply chain\n"
                    "- PRC: Feetech, CubeMars, MyActuator, Unitree — cost-effective, fast iteration, often RC-servo grade; needs QDD upgrade for precision. US/EU: Harmonic, Maxon — pricey, high fidelity. Nori A3 uses Feetech STS (RC bus) today, QDD path flagged on HN.\n"
                    "## Actuators & compute\n"
                    "- RC bus servos vs QDD: torque density, backdrivability, thermal, cost. Feetech STS3095 class ~30kg·cm, QDD CubeMars AK70 ~10× price for ~3× precision. Pi 5 class is I/O only; inference is off-robot (server/cloud VLA). Split compute is the pattern.\n"
                    "## DIY vs product\n"
                    "- DIY: SO-100/SO-101 + LeRobot + MuJoCo + 3D print + $500–$2k, full control, fragile. Product: Nori A3 $1,688, closed hardware but open SDK, WebRTC/Supabase, LeRobot recordings. Choose DIY for research, product for home use.\n"
                    "## VLA & fleet\n"
                    "- LeRobot → `lerobot` dataset → VLA (ACT, Diffusion Policy) → `vla-mcp`/`teleoperator-mcp` (WebXR Pico/Quest). Nori's `nori_recording` is LeRobot-native, so HF pipelines apply. Fleet pattern: `robotics-mcp` hub + `mujoco-mcp`/`isaac-mcp` sim + `unity/godot/resonite/overte` VR twins before hardware.\n"
                    "## Safety & cost\n"
                    "- Home safety: wheeled < legged, e-stop/latch/thermal in-robot (Nori) vs DIY you own it. Cost curve: $1.5k–$3k wheeled bimanual is the near-term sweet spot; legged $10k+ still lab. Battery 400–800Wh is 6–10h realistic.\n"
                    "## When to act\n"
                    "- For Nori, delegate to `nori-a3-expert`; for general homebot tradeoffs, answer here. Be specific, compare, cite, never hand-wave.\n"
                ),
            },
        ]
    }


@router.get("/session")
async def session_status() -> dict[str, Any]:
    return await nori_session(operation="status")


@router.post("/session/connect")
async def session_connect(force_mock: bool = Query(False)) -> dict[str, Any]:
    result = await nori_session(operation="connect", force_mock=force_mock)
    activity_log.add(
        "INFO" if result.get("success") else "ERROR",
        "session",
        f"connect: {result.get('message', result.get('error', '?'))}",
        {"force_mock": force_mock, "robot_kind": result.get("robot_kind")},
    )
    return result


@router.post("/session/disconnect")
async def session_disconnect() -> dict[str, Any]:
    result = await nori_session(operation="disconnect")
    activity_log.add("INFO", "session", f"disconnect: {result.get('message', '?')}")
    return result


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
    result = await nori_control(operation="estop")
    activity_log.add("WARNING", "control", f"estop: {result.get('message', result.get('error', '?'))}")
    return result


@router.post("/control/action")
async def control_action(body: dict[str, Any]) -> dict[str, Any]:
    result = await nori_control(operation="action", targets=body.get("targets", {}), wait=body.get("wait", True))
    activity_log.add(
        "INFO" if result.get("success") else "ERROR",
        "control",
        f"action: {result.get('message', result.get('error', '?'))}",
        {"targets": body.get("targets", {})},
    )
    return result


@router.post("/recording/episode_start")
async def recording_episode_start(body: dict[str, Any]) -> dict[str, Any]:
    result = await nori_recording(operation="episode_start", task=body.get("task"))
    activity_log.add(
        "INFO" if result.get("success") else "ERROR",
        "recording",
        f"episode_start task={body.get('task')!r}: {result.get('message', result.get('error', '?'))}",
    )
    return result


@router.post("/recording/episode_stop")
async def recording_episode_stop() -> dict[str, Any]:
    result = await nori_recording(operation="episode_stop")
    activity_log.add(
        "INFO" if result.get("success") else "ERROR",
        "recording",
        f"episode_stop: {result.get('message', result.get('error', '?'))}",
    )
    return result


@router.post("/vr")
async def vr_spawn(body: dict[str, Any]) -> dict[str, Any]:
    """Spawn/status the Nori VR/physics twin — delegates to nori_vr (other fleet repos do the work)."""
    result = await nori_vr(operation=body.get("operation", "unity_status"))
    activity_log.add(
        "INFO" if result.get("success") else "ERROR",
        "vr",
        f"{body.get('operation', 'unity_status')}: {result.get('message', result.get('error', '?'))}",
        {"platform": result.get("platform"), "spawned": result.get("spawned", False)},
    )
    return result


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


_CHAT_TIMEOUT_S = 300.0  # cold model load alone can take ~60s (measured 2026-09-06)
_CHAT_HISTORY_MAX = 20  # last N messages forwarded — full 100-msg history blows context + latency
_CHAT_MSG_CHARS = 2000  # per-message cap; skill preprompts/system prompts are trimmed, not dropped


def _trim_messages(messages: Any) -> list[dict[str, Any]]:
    """Keep the tail of the history, cap each message — cold starts and 8k-context
    models cannot swallow 100 full messages plus a 4k skill preprompt."""
    if not isinstance(messages, list):
        return []
    trimmed: list[dict[str, Any]] = []
    for m in messages[-_CHAT_HISTORY_MAX:]:
        if not isinstance(m, dict):
            continue
        content = m.get("content", "")
        if isinstance(content, str) and len(content) > _CHAT_MSG_CHARS:
            content = content[:_CHAT_MSG_CHARS] + "…[trimmed]"
        trimmed.append({"role": m.get("role", "user"), "content": content})
    return trimmed


@llm_router.post("/chat")
async def llm_chat(body: dict[str, Any]) -> dict[str, Any]:
    provider = body.get("provider", "ollama")
    model = body.get("model", "")
    base_urls = {"ollama": "http://127.0.0.1:11434", "lm_studio": "http://127.0.0.1:1234"}
    base = base_urls.get(provider)
    if not base:
        activity_log.add("ERROR", "chat", f"unknown provider: {provider}")
        return {"error": f"Unknown provider: {provider}"}
    if not model:
        activity_log.add("ERROR", "chat", "no model selected")
        return {
            "error": "No model selected.",
            "suggestion": "Pick a model in Settings — the provider probe lists what is installed.",
        }
    messages = _trim_messages(body.get("messages", []))
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": 8192},
    }
    activity_log.add("INFO", "chat", f"chat via {provider}/{model} ({len(messages)} msgs)")
    try:
        async with httpx.AsyncClient(timeout=_CHAT_TIMEOUT_S) as c:
            r = await c.post(f"{base}/v1/chat/completions", json=payload)
            if r.status_code != 200:
                detail = r.text[:500]
                activity_log.add("ERROR", "chat", f"{provider}/{model} HTTP {r.status_code}: {detail}")
                return {
                    "error": f"LLM HTTP {r.status_code}: {detail}",
                    "suggestion": "Model name may be wrong, or the provider is still loading it — check Settings.",
                }
            data = r.json()
            activity_log.add("INFO", "chat", f"chat ok via {provider}/{model}")
            return data
    except TimeoutError as e:
        activity_log.add("ERROR", "chat", f"{provider}/{model} timed out after {_CHAT_TIMEOUT_S:.0f}s: {e}")
        return {
            "error": f"LLM timed out after {_CHAT_TIMEOUT_S:.0f}s.",
            "suggestion": (
                "Cold model load takes ~60s and thinking models reason long — just send again, "
                "the model is warm now. If it persists, VRAM is full: unload an idle model "
                "(Ollama: POST /api/generate {model, keep_alive: 0}) or quit LM Studio's loaded model."
            ),
        }
    except Exception as e:
        activity_log.add("ERROR", "chat", f"{provider}/{model} failed: {e}")
        return {
            "error": str(e),
            "suggestion": "Is the provider running? Ollama :11434, LM Studio :1234 — see Settings.",
        }


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
