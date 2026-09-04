"""Process-wide Nori session singleton — real RemoteTeleop or nori_sdk's own MockRobot.

Only one active session at a time (matches nori-sdk's own model: one robot, one operator
channel). Which robot identity a `connect()` uses is decided by robot_profiles.py's
RobotProfileStore, not directly by env vars — real hardware connects via Supabase
signaling when the active (or requested) profile is `kind="physical"`; otherwise every
`nori_session(operation="connect")` call falls back to nori_sdk's own `mock_session()` —
the SDK's upstream-supported, declared mock, not a fleet-invented fake.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from norirobotics_mcp.robot_profiles import RobotProfile

logger = logging.getLogger("norirobotics-mcp.session")

_session: Any | None = None
_session_cm: Any | None = None  # the async-context-manager object, kept for clean __aexit__
_is_mock: bool = True
_active_profile: RobotProfile | None = None


def get_session() -> Any | None:
    return _session


def is_connected() -> bool:
    return _session is not None


def is_mock() -> bool:
    return _is_mock


def current_profile() -> RobotProfile | None:
    """The profile actually backing the live session, or None if not connected."""
    return _active_profile


def current_profile_or_pending() -> RobotProfile | None:
    """The connected session's profile, or - if nothing is connected yet - whichever
    profile is currently marked active in the store (i.e. what WOULD be used on the
    next connect())."""
    if _active_profile is not None:
        return _active_profile
    from norirobotics_mcp.robot_profiles import profile_store

    return profile_store.get(profile_store.active_id())


async def connect(*, force_mock: bool = False, profile_id: str | None = None) -> tuple[Any, bool]:
    """Open a Nori session against the given (or active) robot profile. Returns
    (robot, is_mock). Idempotent — reuses an open session regardless of which
    profile_id was passed (matches the existing "one session at a time" model)."""
    global _session, _session_cm, _is_mock, _active_profile

    if _session is not None:
        return _session, _is_mock

    from norirobotics_mcp.robot_profiles import VIRTUAL_PROFILE_ID, profile_store

    pid = profile_id or profile_store.active_id()
    profile = profile_store.get(pid) or profile_store.get(VIRTUAL_PROFILE_ID)

    use_real = profile is not None and profile.kind == "physical" and not force_mock

    if use_real:
        assert profile is not None  # narrowed by `use_real` above; keeps pyright honest
        from nori_sdk import RemoteTeleop, SupabaseSignaling, UserAuth

        auth = UserAuth(
            profile.supabase_url,
            profile.supabase_anon_key,
            profile.user_email,
            profile.user_password,
        )
        signaling = SupabaseSignaling(
            profile.supabase_url,
            profile.supabase_anon_key,
            room=profile.robot_room,
            token_provider=auth.token,
        )
        cm = RemoteTeleop(signaling)
        robot = await cm.__aenter__()
        _session, _session_cm, _is_mock, _active_profile = robot, cm, False, profile
        logger.info("Connected to real Nori A3 session (profile=%s, room=%s)", profile.name, profile.robot_room)
        return robot, False

    from nori_sdk.mock import mock_session

    # force_mock overriding a physical selection must report as Virtual, not as the
    # physical profile that was requested but deliberately bypassed - otherwise a
    # forced-mock session would misreport robot_kind="physical" downstream.
    effective_profile = (
        profile if (profile is not None and profile.kind == "virtual") else profile_store.get(VIRTUAL_PROFILE_ID)
    )

    cm = mock_session()
    robot = await cm.__aenter__()
    _session, _session_cm, _is_mock, _active_profile = robot, cm, True, effective_profile
    logger.info(
        "Connected to nori_sdk mock_session() (profile=%s)",
        effective_profile.name if effective_profile else "virtual",
    )
    return robot, True


async def disconnect() -> bool:
    global _session, _session_cm, _is_mock, _active_profile

    if _session_cm is None:
        return False
    try:
        await _session_cm.__aexit__(None, None, None)
    finally:
        _session, _session_cm, _is_mock, _active_profile = None, None, True, None
    return True
