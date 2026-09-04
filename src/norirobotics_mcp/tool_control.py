"""Portmanteau nori_control(operation=...) — motion + safety, gated behind an open session.

Motion and safety share one tool because they operate on the same live joint/motor state and
because every DESTRUCTIVE-adjacent op here (estop aside) should be reachable in the same
mental model an operator uses: "move it" and "stop it" are two facets of one control surface.
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import Context

from norirobotics_mcp import session_state

logger = logging.getLogger("norirobotics-mcp.control")


def _error_response(message: str, exc: Exception | None = None) -> dict[str, Any]:
    if exc is not None:
        logger.exception("%s: %s", message, exc)
    else:
        logger.error("%s", message)
    return {
        "success": False,
        "message": message,
        "error": message,
        "error_type": type(exc).__name__ if exc else "ValueError",
    }


_MOTION_OPS = {"jog", "set_jog", "clear_jog", "action", "pose"}
_SAFETY_OPS = {"estop", "estop_confirmed", "reset_latch", "reset_arm"}


async def nori_control(
    ctx: Context | None = None,
    operation: str = "estop",
    payload: dict[str, Any] | None = None,
    targets: dict[str, Any] | None = None,
    side: str | None = None,
    position_m: list[float] | None = None,
    orientation_xyzw: list[float] | None = None,
    arm: str | None = None,
    duration: float | None = None,
    wait: bool = True,
    timeout: float | None = None,
) -> dict[str, Any]:
    """NORI_CONTROL — drive joints/gripper and manage the e-stop/reset safety latch.

    [RATIONALE] Requires an open session (nori_session(operation='connect')). Every op here maps
    1:1 onto a nori_sdk.RemoteTeleop method — this tool does not reinterpret or clamp targets
    beyond what the SDK/robot firmware already does (calibration clamping + stall detection +
    thermal cutoff live in the robot's own protection stack, not here).

    Operations (motion — require `wait_ready` state):
        jog          — fixed-time jog. Args: payload (dict), duration (float, seconds).
        set_jog      — continuous jog until cleared. Args: payload (dict).
        clear_jog    — stop a continuous jog (equivalent to set_jog(payload={})).
        action       — move to target joint/gripper positions. Args: targets (dict), wait (bool).
        pose         — Cartesian gripper pose via on-board IK. Args: side ("left"|"right"),
                       position_m ([x,y,z]), orientation_xyzw ([x,y,z,w], optional), wait (bool).

    Operations (safety — always available once connected):
        estop            — emergency stop. Raises (returned as success=False) on a dead control channel.
        estop_confirmed  — await the robot's e-stop latch confirmation. Args: timeout (float, seconds).
        reset_latch      — clear the e-stop latch after a confirmed stop.
        reset_arm        — reset a single arm's fault state. Args: arm ("left"|"right").

    ## Return Format
    {"success": bool, "message": str, ...operation-specific data}. On failure: error, error_type,
    and — for motion ops issued without a session — a suggestion to connect first.

    ## Examples
    nori_control(operation="estop")
    nori_control(operation="action", targets={"left_gripper": 0.5})
    nori_control(operation="pose", side="left", position_m=[0.3, 0.1, 0.2])
    nori_control(operation="reset_arm", arm="left")
    """
    op = operation.lower().strip()
    logger.info("nori_control(%s)", op)

    robot = session_state.get_session()
    if robot is None:
        return {
            "success": False,
            "message": "No active session.",
            "error": "No active session.",
            "suggestions": ["Call nori_session(operation='connect') before nori_control."],
        }

    try:
        if op == "jog":
            result = await robot.jog(payload or {}, duration=duration if duration is not None else 0.0)
            return {"success": True, "message": "Jog executed.", "result": _jsonable(result)}

        if op == "set_jog":
            result = robot.set_jog(payload or {})
            return {"success": True, "message": "Continuous jog started.", "result": _jsonable(result)}

        if op == "clear_jog":
            result = robot.set_jog(None)
            return {"success": True, "message": "Jog cleared.", "result": _jsonable(result)}

        if op == "action":
            result = await robot.action(targets or {}, wait=wait)
            return {"success": True, "message": "Action targets sent.", "result": _jsonable(result)}

        if op == "pose":
            if not side or position_m is None:
                return _error_response("pose requires 'side' and 'position_m' ([x, y, z]).")
            result = await robot.pose(side, position_m, orientation_xyzw=orientation_xyzw, wait=wait)
            return {"success": True, "message": f"Pose command sent for {side} arm.", "result": _jsonable(result)}

        if op == "estop":
            result = robot.estop()
            return {"success": True, "message": "E-stop triggered.", "result": _jsonable(result)}

        if op == "estop_confirmed":
            result = await robot.estop_confirmed(timeout=timeout if timeout is not None else 5.0)
            return {"success": True, "message": "E-stop confirmed by robot.", "result": _jsonable(result)}

        if op == "reset_latch":
            result = robot.reset_latch()
            return {"success": True, "message": "E-stop latch reset.", "result": _jsonable(result)}

        if op == "reset_arm":
            if not arm:
                return _error_response("reset_arm requires 'arm' ('left' or 'right').")
            result = robot.reset_arm(arm)
            return {"success": True, "message": f"{arm} arm fault state reset.", "result": _jsonable(result)}

        return _error_response(
            f"Unknown operation: {operation}. Motion: {sorted(_MOTION_OPS)}. Safety: {sorted(_SAFETY_OPS)}."
        )
    except Exception as e:
        return _error_response(str(e), exc=e)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)
