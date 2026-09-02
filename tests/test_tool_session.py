from __future__ import annotations

import pytest

from norirobotics_mcp.tool_session import nori_session

pytestmark = pytest.mark.asyncio


async def test_status_when_disconnected():
    result = await nori_session(operation="status")
    assert result["success"] is True
    assert result["connected"] is False


async def test_connect_falls_back_to_mock():
    result = await nori_session(operation="connect")
    assert result["success"] is True
    assert result["connected"] is True
    assert result["mock"] is True


async def test_connect_is_idempotent():
    first = await nori_session(operation="connect")
    second = await nori_session(operation="connect")
    assert first["mock"] is True
    assert second["mock"] is True


async def test_status_when_connected():
    await nori_session(operation="connect")
    result = await nori_session(operation="status")
    assert result["success"] is True
    assert result["connected"] is True


async def test_disconnect():
    await nori_session(operation="connect")
    result = await nori_session(operation="disconnect")
    assert result["success"] is True
    assert result["connected"] is False

    status = await nori_session(operation="status")
    assert status["connected"] is False


async def test_disconnect_when_already_closed():
    result = await nori_session(operation="disconnect")
    assert result["success"] is True
    assert "No active session" in result["message"]


async def test_unknown_operation():
    result = await nori_session(operation="bogus")
    assert result["success"] is False
