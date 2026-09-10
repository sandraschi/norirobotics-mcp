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
from norirobotics_mcp.robot_profiles import provenance_fields

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
_POLICY_OPS = {"policy_stream", "policy_stream_status", "set_leader_action"}


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
    policy_action: str | None = None,
    extra: dict[str, Any] | None = None,
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

    Operations (policy/leader streaming — new in nori-sdk 1.1.0, 2026-09-01):
        policy_stream        — drive the robot's policy streamer. Args: policy_action
                               ("start"|"stop"|"status" — named distinctly from this tool's own
                               `operation` param to avoid confusion with the "action" motion verb
                               above), extra (dict, e.g. {"dest": "laptop"} for "start").
        policy_stream_status — the last policy_stream_status frame seen (property read, no
                               SDK call — the ONLY way to check liveness is polling this or
                               calling policy_stream(policy_action="status")).
        set_leader_action    — absolute pose from a physical leader arm, ONE frame not a stream.
                               Args: targets (dict[str, float] — reuses the same param as 'action' above).

    ## Return Format
    {"success": bool, "message": str, "robot_kind": "physical"|"virtual", "profile_name": str|None
    (policy/leader ops only), ...operation-specific data}. On failure: error, error_type, and —
    for motion ops issued without a session — a suggestion to connect first.

    ## Examples
    nori_control(operation="estop")
    nori_control(operation="action", targets={"left_gripper": 0.5})
    nori_control(operation="pose", side="left", position_m=[0.3, 0.1, 0.2])
    nori_control(operation="reset_arm", arm="left")
    nori_control(operation="policy_stream", policy_action="start", extra={"dest": "laptop"})
    nori_control(operation="set_leader_action", targets={"left_arm_shoulder_pitch": 12.5})
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

        if op == "policy_stream":
            if not policy_action:
                return {
                    "success": False,
                    "message": "policy_stream requires 'policy_action' ('start'|'stop'|'status').",
                    "error": "policy_stream requires 'policy_action'.",
                    **provenance_fields(),
                }
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.policy_stream(policy_action, **kwargs, **(extra or {}))
            return {
                "success": True,
                "message": f"policy_stream({policy_action!r}) executed.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "policy_stream_status":
            result = robot.policy_stream_status
            return {
                "success": True,
                "message": "Policy stream status." if result is not None else "No policy_stream_status seen yet.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "set_leader_action":
            if not targets:
                return {
                    "success": False,
                    "message": "set_leader_action requires 'targets' (dict[str, float]).",
                    "error": "set_leader_action requires 'targets'.",
                    **provenance_fields(),
                }
            robot.set_leader_action(targets)
            return {"success": True, "message": "Leader action frame sent.", **provenance_fields()}

        return _error_response(
            f"Unknown operation: {operation}. Motion: {sorted(_MOTION_OPS)}. Safety: {sorted(_SAFETY_OPS)}. "
            f"Policy: {sorted(_POLICY_OPS)}."
        )
    except Exception as e:
        return _error_response(str(e), exc=e)


def _jsonable(value: Any) -> Any:
    """Recurses into list/tuple/dict elements — see tool_navigation.py's copy of this
    helper for the concrete bug this fixes (a tuple-of-objects field elsewhere silently
    degraded to a str() repr with the non-recursing version)."""
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
