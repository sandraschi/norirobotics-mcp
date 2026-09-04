from __future__ import annotations

from norirobotics_mcp.robot_profiles import VIRTUAL_PROFILE_ID, RobotProfile, RobotProfileStore, slugify


def _store(tmp_path):
    return RobotProfileStore(path=tmp_path / "profiles.json", active_path=tmp_path / "active.json")


def test_seeds_virtual_profile_on_first_use(tmp_path):
    store = _store(tmp_path)
    ids = {p.id for p in store.list()}
    assert VIRTUAL_PROFILE_ID in ids
    assert store.active_id() == VIRTUAL_PROFILE_ID


def test_save_get_delete_roundtrip(tmp_path):
    store = _store(tmp_path)
    profile = RobotProfile(id="mine", name="My A3", kind="physical", robot_room="ROOM-1")
    store.save(profile)

    fetched = store.get("mine")
    assert fetched is not None
    assert fetched.name == "My A3"
    assert fetched.kind == "physical"

    assert store.delete("mine") is True
    assert store.get("mine") is None
    assert store.delete("mine") is False


def test_active_id_falls_back_when_stale(tmp_path):
    store = _store(tmp_path)
    store.set_active("does-not-exist")
    assert store.active_id() == VIRTUAL_PROFILE_ID


def test_active_id_persists_a_real_selection(tmp_path):
    store = _store(tmp_path)
    store.save(RobotProfile(id="mine", name="My A3", kind="virtual"))
    store.set_active("mine")
    assert store.active_id() == "mine"


def test_env_migration_seeds_a_physical_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("NORI_MCP_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("NORI_MCP_SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setenv("NORI_MCP_ROBOT_ROOM", "NORI-A3-0001")

    store = _store(tmp_path)
    physical = [p for p in store.list() if p.kind == "physical"]
    assert len(physical) == 1
    assert physical[0].robot_room == "NORI-A3-0001"
    assert physical[0].supabase_url == "https://example.supabase.co"
    # The migrated profile becomes active since nothing else claimed that slot yet.
    assert store.active_id() == physical[0].id


def test_env_migration_is_idempotent_across_store_reloads(tmp_path, monkeypatch):
    monkeypatch.setenv("NORI_MCP_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("NORI_MCP_SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setenv("NORI_MCP_ROBOT_ROOM", "NORI-A3-0001")

    _store(tmp_path)  # first load seeds it
    store2 = _store(tmp_path)  # second load must not duplicate it
    physical = [p for p in store2.list() if p.kind == "physical"]
    assert len(physical) == 1


def test_slugify():
    assert slugify("Mr. Li's A3") == "mr-li-s-a3"
    assert slugify("  spaces  ") == "spaces"
    assert slugify("") == "profile"
