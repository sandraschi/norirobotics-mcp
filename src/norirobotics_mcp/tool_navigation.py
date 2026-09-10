"""Portmanteau nori_navigation(operation=...) — named waypoint navigation.

New in nori-sdk 1.1.0 (2026-09-01) — this repo never wrapped it until now. Operations map 1:1
onto real nori_sdk.RemoteTeleop methods, verified directly against the installed package
(inspect.signature + a live mock_session() round-trip, not assumed from a changelog).
Requires an open session (nori_session(operation='connect')), same as nori_control/nori_recording.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from norirobotics_mcp import session_state
from norirobotics_mcp.robot_profiles import provenance_fields

logger = logging.getLogger("norirobotics-mcp.navigation")

_OPS = {
    "remember_waypoint",
    "delete_waypoint",
    "list_waypoints",
    "navigate_to_waypoint",
    "goto_pose",
    "cancel_navigation",
    "await_navigation",
    "status",
}


async def nori_navigation(
    ctx: Context | None = None,
    operation: Annotated[
        str,
        Field(
            description="One of 'remember_waypoint', 'delete_waypoint', 'list_waypoints', "
            "'navigate_to_waypoint', 'goto_pose', 'cancel_navigation', 'await_navigation', 'status'."
        ),
    ] = "status",
    name: Annotated[
        str | None,
        Field(description="Waypoint name. Required for remember_waypoint/delete_waypoint/navigate_to_waypoint."),
    ] = None,
    side: Annotated[str | None, Field(description="For 'goto_pose': 'left' or 'right'.")] = None,
    position_m: Annotated[list[float] | None, Field(description="For 'goto_pose': [x, y, z].")] = None,
    orientation_xyzw: Annotated[
        list[float] | None, Field(description="For 'goto_pose': [x, y, z, w], optional.")
    ] = None,
    wait: Annotated[bool, Field(description="For 'goto_pose': await completion. Default True.")] = True,
    goal_id: Annotated[
        str | None,
        Field(
            description="For 'cancel_navigation' (optional — cancels any goal if omitted) and 'await_navigation' (required)."
        ),
    ] = None,
    timeout: Annotated[
        float | None, Field(description="Per-call timeout override in seconds. SDK defaults vary by operation.")
    ] = None,
) -> dict[str, Any]:
    """NORI_NAVIGATION — named waypoint navigation (Nav2 goals under the hood).

    [RATIONALE] Requires an open session. Waypoints are saved against the robot's ACTIVE map —
    `remember_waypoint` captures the robot's current localized pose under a name;
    `navigate_to_waypoint` starts one Nav2 goal to a previously saved destination. This is a
    fresh SDK 1.1.0 capability (2026-09-01) verified against the real installed package, not
    guessed from documentation.

    Operations:
        remember_waypoint    — save the robot's current pose under `name`. Reusing a name replaces it.
        delete_waypoint      — delete a saved destination. Refused while a goal is active.
        list_waypoints       — list destinations saved against the active map.
        navigate_to_waypoint — start ONE Nav2 goal to a saved destination. **This moves the robot.**
        goto_pose            — Cartesian gripper pose via on-board IK (alias for nori_control's
                               'pose' with wait=True defaults) — included here because it shares
                               navigation's on-board-IK path in the SDK, not a duplicate feature.
        cancel_navigation    — cancel the active goal, optionally only if it matches `goal_id`.
        await_navigation     — wait for `goal_id` to reach a terminal state, without polling.
        status (default)     — a fresh navigation snapshot (state, active, distance_remaining_m, etc.).

    ## Return Format
    {"success": bool, "message": str, "robot_kind": "physical"|"virtual", "profile_name": str|None,
    "result": {...NavigationStatus fields, incl. "waypoints" for list_waypoints...}}

    ## Examples
    nori_navigation(operation="remember_waypoint", name="kitchen")
    nori_navigation(operation="navigate_to_waypoint", name="kitchen")
    nori_navigation(operation="list_waypoints")
    nori_navigation(operation="await_navigation", goal_id="...")
    nori_navigation(operation="status")
    """
    op = operation.lower().strip()
    logger.info("nori_navigation(%s)", op)

    robot = session_state.get_session()
    if robot is None:
        return {
            "success": False,
            "error": "No active session.",
            "suggestions": ["Call nori_session(operation='connect') before nori_navigation."],
            **provenance_fields(),
        }

    try:
        if op == "remember_waypoint":
            if not name:
                return {"success": False, "error": "remember_waypoint requires 'name'.", **provenance_fields()}
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.remember_waypoint(name, **kwargs)
            return {
                "success": True,
                "message": f"Waypoint '{name}' saved.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "delete_waypoint":
            if not name:
                return {"success": False, "error": "delete_waypoint requires 'name'.", **provenance_fields()}
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.delete_waypoint(name, **kwargs)
            return {
                "success": True,
                "message": f"Waypoint '{name}' deleted.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "list_waypoints":
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.list_waypoints(**kwargs)
            return {"success": True, "message": "Waypoints listed.", "result": _jsonable(result), **provenance_fields()}

        if op == "navigate_to_waypoint":
            if not name:
                return {"success": False, "error": "navigate_to_waypoint requires 'name'.", **provenance_fields()}
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.navigate_to_waypoint(name, **kwargs)
            return {
                "success": True,
                "message": f"Navigation to '{name}' started.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "goto_pose":
            if not side or position_m is None:
                return {
                    "success": False,
                    "error": "goto_pose requires 'side' and 'position_m' ([x, y, z]).",
                    **provenance_fields(),
                }
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.goto_pose(side, position_m, orientation_xyzw=orientation_xyzw, wait=wait, **kwargs)
            return {
                "success": True,
                "message": f"Pose command sent for {side} arm.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "cancel_navigation":
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.cancel_navigation(goal_id=goal_id, **kwargs)
            return {
                "success": True,
                "message": "Navigation cancelled.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "await_navigation":
            if not goal_id:
                return {"success": False, "error": "await_navigation requires 'goal_id'.", **provenance_fields()}
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.await_navigation(goal_id, **kwargs)
            return {
                "success": True,
                "message": "Navigation reached a terminal state.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "status":
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.get_navigation_status(**kwargs)
            return {
                "success": True,
                "message": "Navigation status fetched.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        return {
            "success": False,
            "error": f"Unknown operation: {operation}. Use: {sorted(_OPS)}.",
            **provenance_fields(),
        }
    except Exception as e:
        logger.exception("nori_navigation(%s)", op)
        return {"success": False, "error": str(e), "error_type": type(e).__name__, **provenance_fields()}


def _jsonable(value: Any) -> Any:
    """Recurses into list/tuple/dict elements, not just the top-level value — needed for
    fields like NavigationStatus.waypoints, a tuple of WaypointSummary objects. The
    non-recursing version (copied from the other nori_* tools, which happen never to
    return a tuple-of-objects field) silently degraded such a tuple to its str() repr
    instead of a proper JSON array — caught by testing this against a real mock_session()
    list_waypoints() call before shipping."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)
