"""Portmanteau nori_perception(operation=...) — LiDAR/IMU/perception sensor streams.

New in nori-sdk 1.1.0 (2026-09-01) — this repo never wrapped it until now. Requires an open
session. lidar_scan/imu_sample/perceive are opt-in feeds: they return None until
configure_sensor_streams turns them on AND a real robot is actually publishing — verified
directly against a live mock_session() (MockRobot never publishes sensor frames, so these
correctly return None there; that is expected SDK behavior, not a gap in this wrapper).

perceive() is a SYNCHRONOUS method on RemoteTeleop (confirmed via
inspect.iscoroutinefunction) despite sitting next to async methods — do not await it.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from norirobotics_mcp import session_state
from norirobotics_mcp.robot_profiles import provenance_fields

logger = logging.getLogger("norirobotics-mcp.perception")

_OPS = {"lidar_scan", "imu_sample", "perceive", "configure_sensor_streams", "status"}


async def nori_perception(
    ctx: Context | None = None,
    operation: Annotated[
        str,
        Field(description="One of 'lidar_scan', 'imu_sample', 'perceive', 'configure_sensor_streams', 'status'."),
    ] = "status",
    lidar_hz: Annotated[float | None, Field(description="For 'configure_sensor_streams'. 0 disables the feed.")] = None,
    imu_hz: Annotated[float | None, Field(description="For 'configure_sensor_streams'. 0 disables the feed.")] = None,
    lidar_max_points: Annotated[int | None, Field(description="For 'configure_sensor_streams'.")] = None,
    timeout: Annotated[
        float | None, Field(description="Per-call timeout override in seconds. SDK defaults vary by operation.")
    ] = None,
) -> dict[str, Any]:
    """NORI_PERCEPTION — opt-in LiDAR/IMU streams and the vision-stack world-state snapshot.

    [RATIONALE] Requires an open session. These feeds are opt-in and off by default —
    `configure_sensor_streams` must enable them before `lidar_scan`/`imu_sample`/`perceive`
    return real data; until then (or against the mock, which never publishes sensor frames)
    they correctly return None. This is a fresh SDK 1.1.0 capability verified against the real
    installed package, not guessed from documentation.

    Operations:
        lidar_scan               — most recent `/scan` sample, or None if the feed is off/silent.
        imu_sample                — most recent `/imu/data` sample, or None if the feed is off/silent.
        perceive                  — latest world-state from the vision stack, or None if none arrived.
        configure_sensor_streams  — turn LiDAR/IMU feeds on/off/up. Args: lidar_hz, imu_hz,
                                    lidar_max_points (at least one required — the SDK's own constraint).
        status (default)          — effective stream settings + whether ROS sees a publisher on each.

    ## Return Format
    {"success": bool, "message": str, "robot_kind": "physical"|"virtual", "profile_name": str|None,
    "result": ...}. `result` is `null` for lidar_scan/imu_sample/perceive when no sample has
    arrived yet — that is a normal, expected state, not an error.

    ## Examples
    nori_perception(operation="configure_sensor_streams", lidar_hz=5.0, imu_hz=20.0)
    nori_perception(operation="lidar_scan")
    nori_perception(operation="perceive")
    nori_perception(operation="status")
    """
    op = operation.lower().strip()
    logger.info("nori_perception(%s)", op)

    robot = session_state.get_session()
    if robot is None:
        return {
            "success": False,
            "error": "No active session.",
            "suggestions": ["Call nori_session(operation='connect') before nori_perception."],
            **provenance_fields(),
        }

    try:
        if op == "lidar_scan":
            result = robot.lidar_scan
            return {
                "success": True,
                "message": "Latest LiDAR scan." if result is not None else "No LiDAR sample yet.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "imu_sample":
            result = robot.imu_sample
            return {
                "success": True,
                "message": "Latest IMU sample." if result is not None else "No IMU sample yet.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "perceive":
            result = robot.perceive()  # synchronous — do not await
            return {
                "success": True,
                "message": "Latest perception snapshot." if result is not None else "No perception snapshot yet.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "configure_sensor_streams":
            if lidar_hz is None and imu_hz is None and lidar_max_points is None:
                return {
                    "success": False,
                    "error": "configure_sensor_streams requires at least one of lidar_hz, imu_hz, lidar_max_points.",
                    **provenance_fields(),
                }
            kwargs: dict[str, Any] = {"lidar_hz": lidar_hz, "imu_hz": imu_hz, "lidar_max_points": lidar_max_points}
            if timeout is not None:
                kwargs["timeout"] = timeout
            result = await robot.configure_sensor_streams(**kwargs)
            return {
                "success": True,
                "message": "Sensor stream configuration applied.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        if op == "status":
            kwargs = {"timeout": timeout} if timeout is not None else {}
            result = await robot.get_sensor_stream_status(**kwargs)
            return {
                "success": True,
                "message": "Sensor stream status fetched.",
                "result": _jsonable(result),
                **provenance_fields(),
            }

        return {
            "success": False,
            "error": f"Unknown operation: {operation}. Use: {sorted(_OPS)}.",
            **provenance_fields(),
        }
    except Exception as e:
        logger.exception("nori_perception(%s)", op)
        return {"success": False, "error": str(e), "error_type": type(e).__name__, **provenance_fields()}


def _jsonable(value: Any) -> Any:
    """Recurses into list/tuple/dict elements — see tool_navigation.py's copy of this
    helper for why (a tuple-of-objects field elsewhere silently degraded to a str() repr
    with the non-recursing version)."""
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
