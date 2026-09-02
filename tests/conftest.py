from __future__ import annotations

import pytest

from norirobotics_mcp import session_state


@pytest.fixture(autouse=True)
async def _clean_session():
    """Ensure no session leaks between tests — nori-sdk models one robot, one operator channel."""
    yield
    await session_state.disconnect()
