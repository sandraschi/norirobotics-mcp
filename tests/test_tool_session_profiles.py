from __future__ import annotations

import pytest

import norirobotics_mcp.robot_profiles as robot_profiles_module
import norirobotics_mcp.tool_session as tool_session_module
from norirobotics_mcp.robot_profiles import RobotProfileStore
from norirobotics_mcp.tool_session import nori_session

pytestmark = pytest.mark.asyncio


@pytest.fixture
def isolated_profile_store(tmp_path, monkeypatch):
    """tool_session.py binds `profile_store` at import time (top-level `from ... import
    profile_store`), so patching robot_profiles.profile_store alone wouldn't reach it -
    both the module attribute (used by session_state.py's lazy imports and
    provenance_fields()) and tool_session's own name need to point at the same isolated
    store for a test to be hermetic."""
    store = RobotProfileStore(path=tmp_path / "profiles.json", active_path=tmp_path / "active.json")
    monkeypatch.setattr(robot_profiles_module, "profile_store", store)
    monkeypatch.setattr(tool_session_module, "profile_store", store)
    return store


async def test_add_virtual_profile(isolated_profile_store):
    result = await nori_session(operation="add_profile", name="Second Twin", kind="virtual")
    assert result["success"] is True
    assert result["profile"]["kind"] == "virtual"

    listed = await nori_session(operation="list_profiles")
    ids = {p["id"] for p in listed["profiles"]}
    assert "second-twin" in ids


async def test_add_physical_profile_rejects_bad_credentials(isolated_profile_store):
    result = await nori_session(
        operation="add_profile",
        name="Bad Robot",
        kind="physical",
        supabase_url="https://x.invalid",
        supabase_anon_key="xxx",
        robot_room="ROOM-X",
    )
    assert result["success"] is False
    assert "Could not connect" in result["error"]

    listed = await nori_session(operation="list_profiles")
    ids = {p["id"] for p in listed["profiles"]}
    assert "bad-robot" not in ids  # rejected credentials must never be persisted


async def test_add_physical_profile_requires_credentials(isolated_profile_store):
    result = await nori_session(operation="add_profile", name="Incomplete", kind="physical")
    assert result["success"] is False
    assert "require" in result["error"].lower()


async def test_switch_profile_updates_active(isolated_profile_store):
    await nori_session(operation="add_profile", name="Second Twin", kind="virtual")
    result = await nori_session(operation="switch_profile", profile_id="second-twin")
    assert result["success"] is True
    assert isolated_profile_store.active_id() == "second-twin"


async def test_switch_profile_unknown_id_fails(isolated_profile_store):
    result = await nori_session(operation="switch_profile", profile_id="ghost")
    assert result["success"] is False


async def test_cannot_remove_virtual_profile(isolated_profile_store):
    result = await nori_session(operation="remove_profile", profile_id="virtual")
    assert result["success"] is False
    assert "Virtual Twin" in result["error"]


async def test_cannot_remove_active_profile(isolated_profile_store):
    await nori_session(operation="add_profile", name="Second Twin", kind="virtual")
    await nori_session(operation="switch_profile", profile_id="second-twin")
    result = await nori_session(operation="remove_profile", profile_id="second-twin")
    assert result["success"] is False
    assert "active profile" in result["error"].lower()


async def test_remove_profile_after_switching_away(isolated_profile_store):
    await nori_session(operation="add_profile", name="Second Twin", kind="virtual")
    result = await nori_session(operation="remove_profile", profile_id="second-twin")
    assert result["success"] is True


async def test_connect_reports_robot_kind_and_profile_name(isolated_profile_store):
    result = await nori_session(operation="connect")
    assert result["robot_kind"] == "virtual"
    assert result["profile_name"] == "Virtual Twin"


async def test_status_reports_provenance_even_when_disconnected(isolated_profile_store):
    result = await nori_session(operation="status")
    assert result["connected"] is False
    assert result["robot_kind"] == "virtual"
    assert result["profile_name"] == "Virtual Twin"


async def test_force_mock_reports_virtual_even_with_physical_profile_active(isolated_profile_store):
    """A connect(force_mock=True) against a selected physical profile must report
    robot_kind='virtual' — reporting the bypassed physical profile's identity here
    would be exactly the ambiguity this whole feature exists to eliminate."""
    from norirobotics_mcp.robot_profiles import RobotProfile

    physical = RobotProfile(
        id="office-a3",
        name="Office A3",
        kind="physical",
        supabase_url="https://example.supabase.co",
        supabase_anon_key="anon-key",
        robot_room="ROOM-X",
    )
    isolated_profile_store.save(physical)
    isolated_profile_store.set_active("office-a3")

    result = await nori_session(operation="connect", force_mock=True)
    assert result["mock"] is True
    assert result["robot_kind"] == "virtual"
    assert result["profile_name"] == "Virtual Twin"
