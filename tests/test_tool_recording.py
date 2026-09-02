from __future__ import annotations

import pytest

from norirobotics_mcp.tool_recording import nori_recording
from norirobotics_mcp.tool_session import nori_session

pytestmark = pytest.mark.asyncio


async def test_recording_without_session_fails_gracefully():
    result = await nori_recording(operation="status")
    assert result["success"] is False
    assert "No active session" in result["error"]


async def test_set_bitrate_missing_kbps():
    await nori_session(operation="connect")
    result = await nori_recording(operation="set_bitrate")
    assert result["success"] is False


async def test_status_when_connected():
    await nori_session(operation="connect")
    result = await nori_recording(operation="status")
    assert result["success"] is True


async def test_unknown_operation():
    await nori_session(operation="connect")
    result = await nori_recording(operation="bogus")
    assert result["success"] is False
    assert "Record verbs" in result["error"]


async def test_set_bitrate_success():
    """Regression: robot.set_video_bitrate() is sync on the real SDK, not a coroutine."""
    await nori_session(operation="connect")
    result = await nori_recording(operation="set_bitrate", kbps=800)
    assert result["success"] is True


async def test_set_paused_success():
    """Regression: robot.set_video_paused() is sync on the real SDK, not a coroutine."""
    await nori_session(operation="connect")
    result = await nori_recording(operation="set_paused", paused=True)
    assert result["success"] is True


async def test_frames_success():
    await nori_session(operation="connect")
    result = await nori_recording(operation="frames")
    assert result["success"] is True
    assert result["camera_layout"] is not None


async def test_episode_start_stop_success():
    """record() IS a real coroutine on the SDK. episode_start actually begins recording;
    session-level 'start' alone does not (verified against nori_sdk's mock RecordState)."""
    await nori_session(operation="connect")
    started = await nori_recording(operation="episode_start", task="pour water into cup")
    assert started["success"] is True
    assert started["result"]["recording"] is True

    stopped = await nori_recording(operation="episode_stop")
    assert stopped["success"] is True
    assert stopped["result"]["recording"] is False
    assert stopped["result"]["episodes_kept"] == 1


async def test_snapshot_no_video_track_fails_fast():
    """The mock session has no video track by default — snapshot() genuinely times out
    against it (real nori_sdk behavior, not a bug). Use a short track_timeout to keep this fast
    and assert the honest failure rather than a fabricated success."""
    await nori_session(operation="connect")
    result = await nori_recording(operation="snapshot", role="head", track_timeout=0.2)
    assert result["success"] is False
    assert "video" in result["error"].lower()
