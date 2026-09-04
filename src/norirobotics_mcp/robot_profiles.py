"""Multi-bot registry: named robot profiles (physical or virtual), one switchable
active profile at a time (matches nori-sdk's own one-robot-one-channel model, same
as session_state.py already assumes).

Same flat-JSON-store pattern as obs-mcp's endpoints.py (OBSEndpoint/OBSEndpointStore)
built earlier this session. "physical vs virtual" is explicit here (the `kind` field),
not inferred from whether Supabase env vars happen to be set - every nori_session/
nori_recording response and every recorded episode needs an unambiguous answer to
"was this real hardware or the mock", and that answer has to survive having more than
one physical robot (e.g. Mr. Li's office A3 vs. a future unit here) in play.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_PROFILES_PATH = _DATA_DIR / "robot_profiles.json"
_ACTIVE_PATH = _DATA_DIR / "robot_profile_active.json"

VIRTUAL_PROFILE_ID = "virtual"


class RobotProfile(BaseModel):
    id: str
    name: str
    kind: Literal["physical", "virtual"]
    supabase_url: str = ""
    supabase_anon_key: str = ""
    robot_room: str = ""
    user_email: str = ""
    user_password: str = ""


class RobotProfileStore:
    """JSON-file-backed CRUD for saved robot profiles, plus which one is active."""

    def __init__(self, path: Path = _PROFILES_PATH, active_path: Path = _ACTIVE_PATH) -> None:
        self._path = path
        self._active_path = active_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")
        self._ensure_seeded()

    def _read_all(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_all(self, items: list[dict[str, Any]]) -> None:
        self._path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def _ensure_seeded(self) -> None:
        """Always guarantee a Virtual Twin profile exists; migrate today's only
        configuration path (.env NORI_MCP_SUPABASE_* vars) into a named physical
        profile once, so existing .env-only users aren't forced to re-onboard."""
        items = self._read_all()
        ids = {i.get("id") for i in items}
        changed = False

        if VIRTUAL_PROFILE_ID not in ids:
            items.append(RobotProfile(id=VIRTUAL_PROFILE_ID, name="Virtual Twin", kind="virtual").model_dump())
            changed = True

        env_url = os.environ.get("NORI_MCP_SUPABASE_URL", "").strip()
        env_key = os.environ.get("NORI_MCP_SUPABASE_ANON_KEY", "").strip()
        env_room = os.environ.get("NORI_MCP_ROBOT_ROOM", "").strip()
        if env_url and env_key and env_room:
            already_migrated = any(i.get("kind") == "physical" and i.get("robot_room") == env_room for i in items)
            if not already_migrated:
                profile_id = f"physical-{slugify(env_room)}"
                items.append(
                    RobotProfile(
                        id=profile_id,
                        name=f"Physical ({env_room})",
                        kind="physical",
                        supabase_url=env_url,
                        supabase_anon_key=env_key,
                        robot_room=env_room,
                        user_email=os.environ.get("NORI_MCP_USER_EMAIL", ""),
                        user_password=os.environ.get("NORI_MCP_USER_PASSWORD", ""),
                    ).model_dump()
                )
                changed = True
                # This profile was already "active" in the old env-var-only model -
                # only claim the active slot if nothing has explicitly chosen one yet.
                if not self._active_path.exists():
                    self.set_active(profile_id)

        if changed:
            self._write_all(items)

    def list(self) -> list[RobotProfile]:
        return [RobotProfile(**p) for p in self._read_all()]

    def get(self, profile_id: str) -> RobotProfile | None:
        for p in self._read_all():
            if p.get("id") == profile_id:
                return RobotProfile(**p)
        return None

    def save(self, profile: RobotProfile) -> RobotProfile:
        items = [p for p in self._read_all() if p.get("id") != profile.id]
        items.append(profile.model_dump())
        self._write_all(items)
        return profile

    def delete(self, profile_id: str) -> bool:
        items = self._read_all()
        remaining = [p for p in items if p.get("id") != profile_id]
        if len(remaining) == len(items):
            return False
        self._write_all(remaining)
        return True

    def active_id(self) -> str:
        try:
            data = json.loads(self._active_path.read_text(encoding="utf-8"))
            active = data.get("active_id", VIRTUAL_PROFILE_ID)
        except (json.JSONDecodeError, FileNotFoundError):
            active = VIRTUAL_PROFILE_ID
        # Guard against a stale active_id pointing at a since-deleted profile.
        if self.get(active) is None:
            return VIRTUAL_PROFILE_ID
        return active

    def set_active(self, profile_id: str) -> None:
        self._active_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_path.write_text(json.dumps({"active_id": profile_id}), encoding="utf-8")


def slugify(name: str) -> str:
    import re

    raw = "".join(c if c.isalnum() else "-" for c in name.strip().lower())
    return re.sub(r"-{2,}", "-", raw).strip("-") or "profile"


profile_store = RobotProfileStore()


def provenance_fields() -> dict[str, Any]:
    """{"robot_kind", "profile_name"} for the currently connected session's profile,
    or - if nothing is connected yet - whichever profile is marked active (i.e. what
    WOULD be used on the next connect()). Stamped onto every nori_session/nori_recording
    response so nothing downstream can confuse mock data with real-hardware data."""
    from norirobotics_mcp import session_state

    profile = session_state.current_profile_or_pending()
    return {
        "robot_kind": profile.kind if profile else "unknown",
        "profile_name": profile.name if profile else None,
    }
