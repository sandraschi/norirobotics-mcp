"""Settings from environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NORI_MCP_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 11970

    # nori-sdk / Supabase signaling — all optional. Absent = mock_session() only.
    supabase_url: str = ""
    supabase_anon_key: str = ""
    robot_room: str = ""  # e.g. "NORI-A3-0001"
    user_email: str = ""
    user_password: str = ""
    connect_timeout_s: float = 15.0

    @property
    def has_real_credentials(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key and self.robot_room)


@lru_cache
def load_settings() -> Settings:
    return Settings()
