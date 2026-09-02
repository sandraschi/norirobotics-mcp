"""Process-wide Nori session singleton — real RemoteTeleop or nori_sdk's own MockRobot.

Only one active session at a time (matches nori-sdk's own model: one robot, one operator
channel). Real hardware connects via Supabase signaling when NORI_MCP_SUPABASE_URL /
NORI_MCP_SUPABASE_ANON_KEY / NORI_MCP_ROBOT_ROOM are set; otherwise every `nori_session(
operation="connect")` call falls back to nori_sdk's own `mock_session()` — the SDK's
upstream-supported, declared mock, not a fleet-invented fake.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("norirobotics-mcp.session")

_session: Any | None = None
_session_cm: Any | None = None  # the async-context-manager object, kept for clean __aexit__
_is_mock: bool = True


def get_session() -> Any | None:
    return _session


def is_connected() -> bool:
    return _session is not None


def is_mock() -> bool:
    return _is_mock


async def connect(*, force_mock: bool = False) -> tuple[Any, bool]:
    """Open a Nori session. Returns (robot, is_mock). Idempotent — reuses an open session."""
    global _session, _session_cm, _is_mock

    if _session is not None:
        return _session, _is_mock

    from norirobotics_mcp.config import load_settings

    settings = load_settings()
    use_real = settings.has_real_credentials and not force_mock

    if use_real:
        from nori_sdk import RemoteTeleop, SupabaseSignaling, UserAuth

        auth = UserAuth(
            settings.supabase_url,
            settings.supabase_anon_key,
            settings.user_email,
            settings.user_password,
        )
        signaling = SupabaseSignaling(
            settings.supabase_url,
            settings.supabase_anon_key,
            room=settings.robot_room,
            token_provider=auth.token,
        )
        cm = RemoteTeleop(signaling)
        robot = await cm.__aenter__()
        _session, _session_cm, _is_mock = robot, cm, False
        logger.info("Connected to real Nori A3 session (room=%s)", settings.robot_room)
        return robot, False

    from nori_sdk.mock import mock_session

    cm = mock_session()
    robot = await cm.__aenter__()
    _session, _session_cm, _is_mock = robot, cm, True
    logger.info("Connected to nori-sdk mock_session() — no NORI_MCP_SUPABASE_* credentials configured")
    return robot, True


async def disconnect() -> bool:
    global _session, _session_cm, _is_mock

    if _session_cm is None:
        return False
    try:
        await _session_cm.__aexit__(None, None, None)
    finally:
        _session, _session_cm, _is_mock = None, None, True
    return True
