from __future__ import annotations

import pytest

from norirobotics_mcp.tool_control import nori_control
from norirobotics_mcp.tool_session import nori_session

pytestmark = pytest.mark.asyncio


async def test_control_without_session_fails_gracefully():
    result = await nori_control(operation="estop")
    assert result["success"] is False
    assert "No active session" in result["error"]


async def test_pose_missing_required_args():
    await nori_session(operation="connect")
    result = await nori_control(operation="pose")
    assert result["success"] is False
    assert "side" in result["error"]


async def test_reset_arm_missing_arm():
    await nori_session(operation="connect")
    result = await nori_control(operation="reset_arm")
    assert result["success"] is False


async def test_unknown_operation():
    await nori_session(operation="connect")
    result = await nori_control(operation="bogus")
    assert result["success"] is False


async def test_estop_success():
    """Regression: robot.estop() is sync on the real SDK, not a coroutine — must not be awaited."""
    await nori_session(operation="connect")
    result = await nori_control(operation="estop")
    assert result["success"] is True


async def test_reset_latch_success():
    await nori_session(operation="connect")
    result = await nori_control(operation="reset_latch")
    assert result["success"] is True


async def test_reset_arm_success():
    await nori_session(operation="connect")
    result = await nori_control(operation="reset_arm", arm="left")
    assert result["success"] is True


async def test_set_jog_and_clear_jog_success():
    await nori_session(operation="connect")
    result = await nori_control(operation="set_jog", payload={})
    assert result["success"] is True
    result = await nori_control(operation="clear_jog")
    assert result["success"] is True


async def test_jog_success():
    """jog() IS a real coroutine on the SDK — must be awaited."""
    await nori_session(operation="connect")
    result = await nori_control(operation="jog", payload={}, duration=0.05)
    assert result["success"] is True
