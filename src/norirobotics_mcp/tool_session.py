"""Portmanteau nori_session(operation=...) — connect/disconnect/status lifecycle.

Wraps nori_sdk.RemoteTeleop (real hardware, WebRTC + Supabase signaling) and
nori_sdk.mock.mock_session (no credentials configured — the SDK's own declared mock).
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import Context

from norirobotics_mcp import session_state
from norirobotics_mcp.config import load_settings

logger = logging.getLogger("norirobotics-mcp.session")


async def nori_session(
    ctx: Context | None = None,
    operation: str = "status",
    force_mock: bool = False,
) -> dict[str, Any]:
    """NORI_SESSION — open/close/inspect the live Nori A3 control session.

    [RATIONALE] Every motion, safety, and recording operation needs an open session first.
    Isolating lifecycle here keeps nori_control/nori_recording free of connection bookkeeping
    and makes the mock-vs-real distinction visible in exactly one place.

    Operations:
        connect      — open a session. Uses real WebRTC/Supabase credentials
                       (NORI_MCP_SUPABASE_URL / NORI_MCP_SUPABASE_ANON_KEY / NORI_MCP_ROBOT_ROOM)
                       when configured; otherwise falls back to nori_sdk's own mock_session().
                       Pass force_mock=true to use the mock even with real credentials set.
        disconnect   — close the active session (no-op if already closed).
        status       — connection state, mock/real flag, robot info/telemetry/camera_layout
                       when connected (default).
        wait_ready   — block (up to configured timeout) until the robot reports ready; returns RobotInfo.

    Args:
        operation (str, required): One of "connect", "disconnect", "status", "wait_ready".
        force_mock (bool): For "connect" only — force nori_sdk.mock.mock_session() even if
            real Supabase credentials are configured. Default False.

    Returns:
        success (bool), message (str), connected (bool), mock (bool), and operation-specific data.
    """
    op = operation.lower().strip()
    logger.info("nori_session(%s)", op)

    try:
        if op == "connect":
            robot, mock = await session_state.connect(force_mock=force_mock)
            info = getattr(robot, "info", None)
            return {
                "success": True,
                "message": (
                    "Connected to nori_sdk mock_session() — no real robot credentials configured."
                    if mock
                    else f"Connected to Nori A3 (room={load_settings().robot_room})."
                ),
                "connected": True,
                "mock": mock,
                "info": _jsonable(info),
            }

        if op == "disconnect":
            was_connected = await session_state.disconnect()
            return {
                "success": True,
                "message": "Session closed." if was_connected else "No active session to close.",
                "connected": False,
            }

        if op == "status":
            robot = session_state.get_session()
            if robot is None:
                return {
                    "success": True,
                    "message": "No active session. Call nori_session(operation='connect') first.",
                    "connected": False,
                    "mock": session_state.is_mock(),
                }
            return {
                "success": True,
                "message": "Session active.",
                "connected": True,
                "mock": session_state.is_mock(),
                "status": _jsonable(getattr(robot, "status", None)),
                "telemetry": _jsonable(getattr(robot, "telemetry", None)),
                "daemon_status": _jsonable(getattr(robot, "daemon_status", None)),
                "camera_layout": _jsonable(getattr(robot, "camera_layout", None)),
            }

        if op == "wait_ready":
            robot = session_state.get_session()
            if robot is None:
                return {
                    "success": False,
                    "error": "No active session. Call nori_session(operation='connect') first.",
                    "connected": False,
                }
            settings = load_settings()
            info = await robot.wait_ready()
            return {
                "success": True,
                "message": "Robot ready.",
                "connected": True,
                "mock": session_state.is_mock(),
                "info": _jsonable(info),
                "timeout_s": settings.connect_timeout_s,
            }

        return {
            "success": False,
            "error": f"Unknown operation: {operation}. Use: connect, disconnect, status, wait_ready.",
        }
    except Exception as e:
        logger.exception("nori_session(%s)", op)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "suggestions": [
                "Run nori_session(operation='connect') before other nori_* tools.",
                "Check NORI_MCP_SUPABASE_URL / NORI_MCP_SUPABASE_ANON_KEY / NORI_MCP_ROBOT_ROOM in .env "
                "if you expected a real-robot connection instead of mock.",
            ],
        }


def _jsonable(value: Any) -> Any:
    """Best-effort conversion of nori_sdk dataclasses/pydantic objects to plain JSON-safe data."""
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)
