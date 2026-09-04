"""Portmanteau nori_recording(operation=...) — episode recording, video, LeRobot dataset export path.

`operation` maps 1:1 onto nori_sdk's own RecordVerb literal plus the video/snapshot methods —
deliberately NOT a fleet-invented "start/stop a task by name" abstraction. Verified against the
installed nori_sdk package: RemoteTeleop.record(action: RecordVerb, task="") is a real coroutine;
RecordVerb = "session_start" | "episode_start" | "episode_stop" | "episode_discard" |
"session_end" | "session_discard" | "status" | "start" | "stop" | "discard" | "discard_last".
`session_*` brackets a whole capture session; `episode_*` brackets one episode's actual
recording within that session; `start`/`stop`/`discard` are simpler top-level equivalents.
Episodes persist server-side in LeRobot-compatible format.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, get_args

from fastmcp import Context
from nori_sdk import protocol
from pydantic import Field

from norirobotics_mcp import session_state
from norirobotics_mcp.robot_profiles import provenance_fields

logger = logging.getLogger("norirobotics-mcp.recording")

_RECORD_VERBS: set[str] = set(get_args(protocol.RecordVerb))


async def nori_recording(
    ctx: Context | None = None,
    operation: Annotated[
        str,
        Field(
            description="One of the record verbs (session_start, episode_start, episode_stop, "
            "episode_discard, session_end, session_discard, start, stop, discard, discard_last, "
            "status) or the video ops snapshot/frames/set_bitrate/set_paused."
        ),
    ] = "status",
    task: Annotated[
        str | None,
        Field(description="Episode description. Only meaningful with *_start verbs."),
    ] = None,
    role: Annotated[
        str | None,
        Field(description="Camera role for snapshot, e.g. 'head', 'gripper_left', 'gripper_right'."),
    ] = None,
    kbps: Annotated[int | None, Field(description="Required for set_bitrate.")] = None,
    paused: Annotated[bool | None, Field(description="Required for set_paused.")] = None,
    track_timeout: Annotated[
        float,
        Field(
            description="Seconds to wait for a video track before snapshot fails. Default 20.0 "
            "(nori_sdk's own default). The mock session has no video track by default, so "
            "snapshot() genuinely times out against it unless you lower this for a fast negative test."
        ),
    ] = 20.0,
) -> dict[str, Any]:
    """NORI_RECORDING — control episode/session recording state, video snapshot/bitrate.

    [RATIONALE] Requires an open session (nori_session(operation='connect')). `operation` for the
    record-verb group maps 1:1 onto nori_sdk's own RecordVerb literal — not a fleet-invented
    "start/stop a named task" abstraction, because the SDK already distinguishes a *session*
    (the whole capture run) from an *episode* (one demonstration within it), and getting that
    distinction wrong silently drops or misattributes recorded data.

    Operations (record verbs — passed straight to nori_sdk's RemoteTeleop.record):
        session_start    — open a capture session (does not itself start recording video)
        episode_start     — begin recording one episode within the open session. Args: task (str).
        episode_stop      — end the current episode recording.
        episode_discard    — discard the current (unfinished) episode.
        session_end        — close the capture session, keeping recorded episodes.
        session_discard      — close the capture session, discarding all episodes in it.
        start              — open a session and arm recording (simpler top-level equivalent).
        stop               — stop whatever is currently active (episode or session).
        discard            — discard whatever is currently active.
        discard_last       — discard the most recently completed episode.
        status (default)    — current RecordState (recording bool, session_open, episodes_kept, free_gb).

    Operations (video, separate from the record-verb group):
        snapshot           — grab a single still frame. Args: role (str, e.g. "head", "gripper_left").
        frames              — return the camera_layout (bounded — not a video stream).
        set_bitrate         — adjust live video bitrate. Args: kbps (int).
        set_paused          — pause/resume the live video stream. Args: paused (bool).

    ## Return Format
    {"success": bool, "message": str, "robot_kind": "physical"|"virtual", "profile_name": str|None,
    ...operation-specific data}. On an unrecognized record verb, the error lists the exact valid
    set from nori_sdk.protocol.RecordVerb. robot_kind/profile_name always reflect the connected
    session's actual robot profile — check this before trusting an episode as real-hardware data.

    ## Examples
    nori_recording(operation="episode_start", task="pour water into cup")
    nori_recording(operation="episode_stop")
    nori_recording(operation="snapshot", role="head")
    nori_recording(operation="status")
    """
    op = operation.lower().strip()
    logger.info("nori_recording(%s)", op)

    robot = session_state.get_session()
    if robot is None:
        return {
            "success": False,
            "error": "No active session.",
            "suggestions": ["Call nori_session(operation='connect') before nori_recording."],
            **provenance_fields(),
        }

    try:
        if op in _RECORD_VERBS:
            # NOTE: nori_sdk's RemoteTeleop.record(action, task="") has no metadata kwarg
            # to embed robot_kind/profile_name into the on-disk LeRobot dataset itself -
            # verified against the installed SDK signature, not assumed. Provenance is
            # stamped on this tool's own response below; if nori_sdk grows a metadata hook
            # later, thread it through here too.
            result = await robot.record(op, task=task or "")
            return {
                "success": True,
                "message": f"record({op!r}) executed.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "snapshot":
            result = await robot.snapshot(role=role, track_timeout=track_timeout)
            return {
                "success": True,
                "message": f"Snapshot captured{f' ({role})' if role else ''}.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "frames":
            layout = getattr(robot, "camera_layout", None)
            return {
                "success": True,
                "message": "Camera layout (bounded — not a video stream).",
                "camera_layout": _jsonable(layout),
                **provenance_fields(),
            }

        if op == "set_bitrate":
            if kbps is None:
                return {"success": False, "error": "set_bitrate requires 'kbps'.", **provenance_fields()}
            result = robot.set_video_bitrate(kbps)
            return {
                "success": True,
                "message": f"Video bitrate set to {kbps} kbps.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "set_paused":
            if paused is None:
                return {"success": False, "error": "set_paused requires 'paused' (bool).", **provenance_fields()}
            result = robot.set_video_paused(paused)
            return {
                "success": True,
                "message": f"Video {'paused' if paused else 'resumed'}.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        return {
            "success": False,
            "error": (
                f"Unknown operation: {operation}. Record verbs: {sorted(_RECORD_VERBS)}. "
                "Video ops: snapshot, frames, set_bitrate, set_paused."
            ),
            **provenance_fields(),
        }
    except Exception as e:
        logger.exception("nori_recording(%s)", op)
        return {"success": False, "error": str(e), "error_type": type(e).__name__, **provenance_fields()}


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
    if hasattr(value, "_asdict"):
        return value._asdict()
    return str(value)
