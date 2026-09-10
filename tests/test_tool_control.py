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


async def test_policy_stream_requires_policy_action():
    await nori_session(operation="connect")
    result = await nori_control(operation="policy_stream")
    assert result["success"] is False
    assert "policy_action" in result["error"]


async def test_policy_stream_start_and_status():
    await nori_session(operation="connect")
    result = await nori_control(operation="policy_stream", policy_action="start", extra={"dest": "laptop"})
    assert result["success"] is True
    assert result["result"]["streaming"] is True
    assert result["robot_kind"] == "virtual"

    result = await nori_control(operation="policy_stream", policy_action="status")
    assert result["success"] is True


async def test_policy_stream_status_property_read():
    """No SDK call — reads robot.policy_stream_status directly, matching the SDK's own
    'the ONLY way to check liveness' framing for the polling case."""
    await nori_session(operation="connect")
    await nori_control(operation="policy_stream", policy_action="start")
    result = await nori_control(operation="policy_stream_status")
    assert result["success"] is True


async def test_set_leader_action_requires_targets():
    await nori_session(operation="connect")
    result = await nori_control(operation="set_leader_action")
    assert result["success"] is False
    assert "targets" in result["error"]


async def test_set_leader_action_success():
    """set_leader_action is a fire-and-forget sync call (-> None) — reuses the same
    'targets' param as the 'action' operation above, not a new param."""
    await nori_session(operation="connect")
    result = await nori_control(operation="set_leader_action", targets={"left_arm_shoulder_pitch": 12.5})
    assert result["success"] is True
    assert result["robot_kind"] == "virtual"
