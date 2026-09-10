from __future__ import annotations

import pytest

from norirobotics_mcp.tool_navigation import nori_navigation
from norirobotics_mcp.tool_session import nori_session

pytestmark = pytest.mark.asyncio


async def test_navigation_without_session_fails_gracefully():
    result = await nori_navigation(operation="status")
    assert result["success"] is False
    assert "No active session" in result["error"]


async def test_status_default_operation():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="status")
    assert result["success"] is True
    assert result["robot_kind"] == "virtual"
    assert "state" in result["result"]


async def test_remember_and_list_waypoints():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="remember_waypoint", name="kitchen")
    assert result["success"] is True

    result = await nori_navigation(operation="list_waypoints")
    assert result["success"] is True
    # Regression: waypoints is a tuple of WaypointSummary objects — must come back as a
    # real JSON list of dicts, not a stringified tuple repr (see _jsonable's docstring).
    waypoints = result["result"]["waypoints"]
    assert isinstance(waypoints, list)
    assert any(w["name"] == "kitchen" for w in waypoints)


async def test_remember_waypoint_requires_name():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="remember_waypoint")
    assert result["success"] is False
    assert "name" in result["error"]


async def test_delete_waypoint():
    await nori_session(operation="connect")
    await nori_navigation(operation="remember_waypoint", name="kitchen")
    result = await nori_navigation(operation="delete_waypoint", name="kitchen")
    assert result["success"] is True

    result = await nori_navigation(operation="list_waypoints")
    assert not any(w["name"] == "kitchen" for w in result["result"]["waypoints"])


async def test_navigate_to_waypoint():
    await nori_session(operation="connect")
    await nori_navigation(operation="remember_waypoint", name="kitchen")
    result = await nori_navigation(operation="navigate_to_waypoint", name="kitchen")
    assert result["success"] is True


async def test_navigate_to_waypoint_requires_name():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="navigate_to_waypoint")
    assert result["success"] is False
    assert "name" in result["error"]


async def test_goto_pose_requires_side_and_position():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="goto_pose")
    assert result["success"] is False
    assert "side" in result["error"]


async def test_goto_pose_success():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="goto_pose", side="left", position_m=[0.3, 0.1, 0.2])
    assert result["success"] is True


async def test_cancel_navigation():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="cancel_navigation")
    assert result["success"] is True


async def test_await_navigation_requires_goal_id():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="await_navigation")
    assert result["success"] is False
    assert "goal_id" in result["error"]


async def test_unknown_operation():
    await nori_session(operation="connect")
    result = await nori_navigation(operation="bogus")
    assert result["success"] is False
