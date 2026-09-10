from __future__ import annotations

import pytest

from norirobotics_mcp.tool_perception import nori_perception
from norirobotics_mcp.tool_session import nori_session

pytestmark = pytest.mark.asyncio


async def test_perception_without_session_fails_gracefully():
    result = await nori_perception(operation="status")
    assert result["success"] is False
    assert "No active session" in result["error"]


async def test_status_default_operation():
    await nori_session(operation="connect")
    result = await nori_perception(operation="status")
    assert result["success"] is True
    assert result["robot_kind"] == "virtual"


async def test_lidar_scan_returns_none_against_mock():
    """MockRobot never publishes /scan — this is the correct, documented SDK behavior
    ('None if the feed is off or silent'), not a bug in this wrapper."""
    await nori_session(operation="connect")
    result = await nori_perception(operation="lidar_scan")
    assert result["success"] is True
    assert result["result"] is None


async def test_imu_sample_returns_none_against_mock():
    await nori_session(operation="connect")
    result = await nori_perception(operation="imu_sample")
    assert result["success"] is True
    assert result["result"] is None


async def test_perceive_returns_none_against_mock_and_is_not_awaited():
    """Regression: perceive() is a SYNCHRONOUS method on RemoteTeleop despite sitting next
    to async methods — `await robot.perceive()` raises TypeError('object NoneType can't be
    used in an await expression') against the mock. Confirmed via inspect.iscoroutinefunction
    before writing the wrapper. This test would fail loudly if that regressed."""
    await nori_session(operation="connect")
    result = await nori_perception(operation="perceive")
    assert result["success"] is True
    assert result["result"] is None


async def test_configure_sensor_streams_requires_at_least_one_arg():
    await nori_session(operation="connect")
    result = await nori_perception(operation="configure_sensor_streams")
    assert result["success"] is False
    assert "requires" in result["error"]


async def test_configure_sensor_streams_success():
    await nori_session(operation="connect")
    result = await nori_perception(operation="configure_sensor_streams", lidar_hz=5.0, imu_hz=20.0)
    assert result["success"] is True
    assert result["result"]["ok"] is True
    assert result["result"]["lidar_hz"] == 5.0


async def test_unknown_operation():
    await nori_session(operation="connect")
    result = await nori_perception(operation="bogus")
    assert result["success"] is False
