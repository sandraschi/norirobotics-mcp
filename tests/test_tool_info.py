from __future__ import annotations

import pytest

from norirobotics_mcp.tool_info import nori_info

pytestmark = pytest.mark.asyncio


async def test_info_default():
    result = await nori_info()
    assert result["success"] is True
    assert result["product"] == "Nori A3"


async def test_specs():
    result = await nori_info(operation="specs")
    assert result["success"] is True
    assert result["data"]["specs"]["dof"] == 19


async def test_sdk_links():
    result = await nori_info(operation="sdk_links")
    assert result["success"] is True
    assert "nori-sdk-py" in result["data"]["sdk_repo"]


async def test_predecessor():
    result = await nori_info(operation="predecessor")
    assert result["success"] is True
    assert "XLeRobot" in result["data"]["summary"]


async def test_community():
    result = await nori_info(operation="community")
    assert result["success"] is True
    assert len(result["data"]["praise"]) > 0
    assert len(result["data"]["criticism"]) > 0


async def test_actuator_upgrade():
    result = await nori_info(operation="actuator_upgrade")
    assert result["success"] is True
    assert any(c["vendor"] == "CubeMars" for c in result["data"]["candidates_named_on_hn"])


async def test_fleet_peers():
    result = await nori_info(operation="fleet_peers")
    assert result["success"] is True
    ids = {p["id"] for p in result["peers"]}
    assert "robotics-mcp" in ids
    assert "vla-mcp" in ids


async def test_unknown_operation():
    result = await nori_info(operation="bogus")
    assert result["success"] is False
    assert "Unknown operation" in result["error"]
