"""Portmanteau nori_info(operation=...) — specs, SDK links, lineage, community, fleet map.

No live session required; this is the "read the room before you touch the robot" tool.
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import Context

from norirobotics_mcp.knowledge import (
    ACTUATOR_UPGRADE_NOTES,
    COMMUNITY_REACTION,
    FLEET_PEERS,
    NORI_HERO,
    PREDECESSOR,
    SDK_LINKS,
)

logger = logging.getLogger("norirobotics-mcp.info")


async def nori_info(
    ctx: Context | None = None,
    operation: str = "info",
) -> dict[str, Any]:
    """NORI_INFO — Nori A3 hero specs, SDK links, hardware lineage, HN community reaction, fleet map.

    [RATIONALE] Single read-only entry point for "what is this robot and where does it come from" —
    kept separate from nori_session/nori_control/nori_recording so an agent can answer these questions
    without ever opening a live robot session (real or mock).

    Operations:
        info              — tagline + vendor + key specs (default)
        specs             — full structured hero spec dict
        sdk_links         — nori-sdk-py repo, PyPI package, protocol, dataset format, license
        predecessor       — XLeRobot lineage and what carried forward to the from-scratch A3 design
        community         — Hacker News launch-thread reaction (praise + criticism, summarized)
        actuator_upgrade  — HN-sourced note on RC-servo-vs-QDD actuator upgrade path (no fabricated BOM)
        fleet_peers       — sandraschi robotics-mcp fleet members relevant to Nori integration

    Returns:
        success (bool), message (str), and operation-specific data.
    """
    op = operation.lower().strip()
    logger.info("nori_info(%s)", op)

    try:
        if op == "info":
            return {
                "success": True,
                "message": NORI_HERO["tagline"],
                "product": NORI_HERO["product"],
                "vendor": NORI_HERO["vendor"],
                "price_usd": NORI_HERO["price_usd"],
                "ships": NORI_HERO["ships"],
                "specs_summary": NORI_HERO["specs"],
            }

        if op == "specs":
            return {"success": True, "message": "Full Nori A3 hero spec sheet.", "data": NORI_HERO}

        if op == "sdk_links":
            return {
                "success": True,
                "message": "nori-sdk-py repo, PyPI package, protocol, and license.",
                "data": SDK_LINKS,
            }

        if op == "predecessor":
            return {"success": True, "message": PREDECESSOR["summary"], "data": PREDECESSOR}

        if op == "community":
            return {
                "success": True,
                "message": f"Hacker News launch reaction: {len(COMMUNITY_REACTION['praise'])} praise points, "
                f"{len(COMMUNITY_REACTION['criticism'])} criticism points.",
                "data": COMMUNITY_REACTION,
            }

        if op == "actuator_upgrade":
            return {
                "success": True,
                "message": ACTUATOR_UPGRADE_NOTES["summary"],
                "data": ACTUATOR_UPGRADE_NOTES,
            }

        if op == "fleet_peers":
            return {
                "success": True,
                "message": "Fleet MCPs relevant to Nori A3 integration.",
                "peers": FLEET_PEERS,
            }

        return {
            "success": False,
            "error": (
                f"Unknown operation: {operation}. Use: info, specs, sdk_links, predecessor, "
                "community, actuator_upgrade, fleet_peers."
            ),
        }
    except Exception as e:
        logger.exception("nori_info(%s)", op)
        return {"success": False, "error": str(e), "error_type": type(e).__name__}
