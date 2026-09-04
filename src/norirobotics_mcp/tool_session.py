"""Portmanteau nori_session(operation=...) — connect/disconnect/status lifecycle,
plus the multi-bot profile registry (list/add/switch/remove).

Wraps nori_sdk.RemoteTeleop (real hardware, WebRTC + Supabase signaling) and
nori_sdk.mock.mock_session (no credentials configured — the SDK's own declared mock).
Which identity `connect` uses is decided by robot_profiles.py's RobotProfileStore, not
directly by env vars — every response stamps an explicit robot_kind/profile_name so
nothing downstream can confuse a physical A3 (e.g. Mr. Li's office unit) with the
Virtual Twin mock.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from norirobotics_mcp import session_state
from norirobotics_mcp.config import load_settings
from norirobotics_mcp.robot_profiles import VIRTUAL_PROFILE_ID, RobotProfile, profile_store, provenance_fields, slugify

logger = logging.getLogger("norirobotics-mcp.session")


async def nori_session(
    ctx: Context | None = None,
    operation: Annotated[
        str,
        Field(
            description="One of 'connect', 'disconnect', 'status', 'wait_ready', 'list_profiles', "
            "'add_profile', 'switch_profile', 'remove_profile'."
        ),
    ] = "status",
    force_mock: Annotated[
        bool,
        Field(
            description="For 'connect' only — force nori_sdk.mock.mock_session() even if the "
            "selected profile is physical. Default False."
        ),
    ] = False,
    profile_id: Annotated[
        str | None,
        Field(
            description="For 'connect' — which saved profile to use (defaults to the active one). "
            "For 'switch_profile'/'remove_profile' — the target profile id. For 'add_profile' — an "
            "optional custom id (defaults to a slug of 'name')."
        ),
    ] = None,
    name: Annotated[str | None, Field(description="For 'add_profile' — display name, e.g. 'Mr. Li's A3'.")] = None,
    kind: Annotated[
        str | None,
        Field(description="For 'add_profile' — 'physical' or 'virtual'."),
    ] = None,
    supabase_url: Annotated[str | None, Field(description="For 'add_profile' with kind='physical'.")] = None,
    supabase_anon_key: Annotated[str | None, Field(description="For 'add_profile' with kind='physical'.")] = None,
    robot_room: Annotated[
        str | None, Field(description="For 'add_profile' with kind='physical', e.g. 'NORI-A3-0001'.")
    ] = None,
    user_email: Annotated[str | None, Field(description="For 'add_profile' with kind='physical'.")] = None,
    user_password: Annotated[str | None, Field(description="For 'add_profile' with kind='physical'.")] = None,
) -> dict[str, Any]:
    """NORI_SESSION — open/close/inspect the live Nori A3 control session, and manage
    the multi-bot profile registry (Virtual Twin plus any number of named physical
    A3s, e.g. one per real owner/site).

    [RATIONALE] Every motion, safety, and recording operation needs an open session first.
    Isolating lifecycle here keeps nori_control/nori_recording free of connection bookkeeping
    and makes the mock-vs-real distinction visible in exactly one place — including which of
    potentially several real robots was used, not just a bare true/false.

    Operations:
        connect        — open a session against the given (or active) profile. Uses real
                       WebRTC/Supabase credentials when the profile is kind="physical";
                       otherwise falls back to nori_sdk's own mock_session(). Pass
                       force_mock=true to use the mock even against a physical profile.
        disconnect   — close the active session (no-op if already closed).
        status       — connection state, robot_kind/profile_name, robot info/telemetry/
                       camera_layout when connected (default).
        wait_ready   — block (up to configured timeout) until the robot reports ready; returns RobotInfo.
        list_profiles  — every saved robot profile plus which one is active.
        add_profile    — save a new profile. kind="virtual" needs only name. kind="physical"
                       needs name/supabase_url/supabase_anon_key/robot_room (user_email/
                       user_password optional) — the credentials are live-tested with a
                       real connect/disconnect round-trip before saving; bad credentials
                       are rejected, not silently stored.
        switch_profile — set which profile future connect() calls default to. Does not
                       reconnect an already-open session — call disconnect then connect
                       to actually switch robots mid-session.
        remove_profile — delete a saved profile. Refuses to remove the active profile or
                       the built-in Virtual Twin.

    ## Return Format
    {"success": bool, "message": str, "connected": bool, "mock": bool, "robot_kind":
    "physical"|"virtual", "profile_name": str|None, ...operation-specific data}

    ## Examples
    nori_session(operation="connect")
    nori_session(operation="connect", profile_id="physical-nori-a3-0001")
    nori_session(operation="add_profile", name="Mr. Li's A3", kind="physical",
                 supabase_url="https://...", supabase_anon_key="...", robot_room="NORI-A3-0001")
    nori_session(operation="list_profiles")
    nori_session(operation="switch_profile", profile_id="virtual")
    nori_session(operation="status")
    """
    op = operation.lower().strip()
    logger.info("nori_session(%s)", op)

    try:
        if op == "connect":
            robot, mock = await session_state.connect(force_mock=force_mock, profile_id=profile_id)
            info = getattr(robot, "info", None)
            profile = session_state.current_profile()
            return {
                "success": True,
                "message": (
                    f"Connected to nori_sdk mock_session() (profile={profile.name if profile else 'Virtual Twin'})."
                    if mock
                    else f"Connected to Nori A3 '{profile.name}' (room={profile.robot_room})."
                ),
                "connected": True,
                "mock": mock,
                **provenance_fields(),
                "info": _jsonable(info),
            }

        if op == "disconnect":
            was_connected = await session_state.disconnect()
            return {
                "success": True,
                "message": "Session closed." if was_connected else "No active session to close.",
                "connected": False,
                **provenance_fields(),
            }

        if op == "status":
            robot = session_state.get_session()
            if robot is None:
                return {
                    "success": True,
                    "message": "No active session. Call nori_session(operation='connect') first.",
                    "connected": False,
                    "mock": session_state.is_mock(),
                    **provenance_fields(),
                }
            return {
                "success": True,
                "message": "Session active.",
                "connected": True,
                "mock": session_state.is_mock(),
                **provenance_fields(),
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
                **provenance_fields(),
                "info": _jsonable(info),
                "timeout_s": settings.connect_timeout_s,
            }

        if op == "list_profiles":
            return {
                "success": True,
                "profiles": [p.model_dump() for p in profile_store.list()],
                "active_profile_id": profile_store.active_id(),
            }

        if op == "add_profile":
            if not name:
                return {"success": False, "error": "add_profile requires 'name'."}
            if kind not in ("physical", "virtual"):
                return {"success": False, "error": "add_profile requires kind='physical' or 'virtual'."}
            pid = profile_id or slugify(name)

            if kind == "virtual":
                candidate = RobotProfile(id=pid, name=name, kind="virtual")
                profile_store.save(candidate)
                return {
                    "success": True,
                    "message": f"Virtual profile '{name}' added.",
                    "profile": candidate.model_dump(),
                }

            if not (supabase_url and supabase_anon_key and robot_room):
                return {
                    "success": False,
                    "error": "Physical profiles require supabase_url, supabase_anon_key, and robot_room.",
                }
            candidate = RobotProfile(
                id=pid,
                name=name,
                kind="physical",
                supabase_url=supabase_url,
                supabase_anon_key=supabase_anon_key,
                robot_room=robot_room,
                user_email=user_email or "",
                user_password=user_password or "",
            )
            test = await _test_physical_connection(candidate)
            if not test["ok"]:
                return {
                    "success": False,
                    "error": f"Could not connect with these credentials: {test['error']}",
                    "suggestions": [
                        "Double-check supabase_url/supabase_anon_key/robot_room/user_email/user_password.",
                        "Confirm the robot is powered on and its Supabase signaling room matches robot_room.",
                    ],
                }
            profile_store.save(candidate)
            return {
                "success": True,
                "message": f"Physical profile '{name}' added and verified live.",
                "profile": candidate.model_dump(),
            }

        if op == "switch_profile":
            if not profile_id:
                return {"success": False, "error": "switch_profile requires 'profile_id'."}
            target = profile_store.get(profile_id)
            if target is None:
                return {"success": False, "error": f"No profile with id '{profile_id}'."}
            profile_store.set_active(profile_id)
            return {
                "success": True,
                "message": f"Active profile set to '{target.name}'. Call disconnect then connect to switch a live session.",
                "active_profile": target.model_dump(),
            }

        if op == "remove_profile":
            if not profile_id:
                return {"success": False, "error": "remove_profile requires 'profile_id'."}
            if profile_id == VIRTUAL_PROFILE_ID:
                return {"success": False, "error": "Cannot remove the built-in Virtual Twin profile."}
            if profile_id == profile_store.active_id():
                return {
                    "success": False,
                    "error": "Cannot remove the active profile — switch to another profile first.",
                }
            removed = profile_store.delete(profile_id)
            return {
                "success": removed,
                "message": "Profile removed." if removed else f"No profile with id '{profile_id}'.",
            }

        return {
            "success": False,
            "error": (
                f"Unknown operation: {operation}. Use: connect, disconnect, status, wait_ready, "
                "list_profiles, add_profile, switch_profile, remove_profile."
            ),
        }
    except Exception as e:
        logger.exception("nori_session(%s)", op)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "suggestions": [
                "Run nori_session(operation='connect') before other nori_* tools.",
                "Run nori_session(operation='list_profiles') to see saved robots, or 'add_profile' "
                "to register a new physical A3 or Virtual Twin.",
            ],
        }


async def _test_physical_connection(profile: RobotProfile, *, timeout: float = 15.0) -> dict[str, Any]:
    """Live credential check for a candidate physical profile — opens its OWN
    RemoteTeleop, independent of session_state's process-wide singleton, so testing a
    new profile never disturbs whatever session is already connected.

    RemoteTeleop.__aenter__() does NOT block on the actual handshake — it returns
    immediately and connects in the background (confirmed by direct testing: bad
    credentials still produced a successful __aenter__ with info=None, plus a
    'getaddrinfo failed' printed internally by nori_sdk rather than raised). The only
    real signal that a connection actually succeeded is wait_ready() completing before
    its timeout — that's what nori_session's own 'wait_ready' operation exists for, so
    reuse it here instead of trusting __aenter__ alone."""
    try:
        from nori_sdk import RemoteTeleop, SupabaseSignaling, UserAuth

        auth = UserAuth(profile.supabase_url, profile.supabase_anon_key, profile.user_email, profile.user_password)
        signaling = SupabaseSignaling(
            profile.supabase_url, profile.supabase_anon_key, room=profile.robot_room, token_provider=auth.token
        )
        async with RemoteTeleop(signaling) as robot:
            info = await robot.wait_ready(timeout=timeout)
            return {"ok": True, "info": _jsonable(info)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _jsonable(value: Any) -> Any:
    """Best-effort conversion of nori_sdk dataclasses/pydantic objects to plain JSON-safe data."""
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)
