"""FastMCP 3.4 — Nori Robotics A3 bimanual home robot MCP."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from norirobotics_mcp import session_state
from norirobotics_mcp.tool_control import nori_control
from norirobotics_mcp.tool_info import nori_info
from norirobotics_mcp.tool_recording import nori_recording
from norirobotics_mcp.tool_session import nori_session

mcp = FastMCP(
    "norirobotics-mcp",
    instructions=(
        "Nori Robotics A3 (19-DOF wheeled bimanual home robot, ships Fall 2026): "
        "use nori_info(operation=...) for specs/SDK/lineage/community facts (no session needed), "
        "nori_session(operation='connect') to open a control session (real robot when "
        "NORI_MCP_SUPABASE_* env vars are set, otherwise nori_sdk's own mock_session()), "
        "then nori_control for motion/safety and nori_recording for LeRobot-format episode capture. "
        "Always call nori_session(operation='connect') before nori_control/nori_recording."
    ),
)

mcp.tool()(nori_info)
mcp.tool()(nori_session)
mcp.tool()(nori_control)
mcp.tool()(nori_recording)


@mcp.tool()
async def nori_help() -> dict[str, Any]:
    """NORI_HELP — quick reference for norirobotics-mcp's four tools and typical call order.

    Returns:
        success (bool), message (str), tools (list of {name, purpose}), typical_flow (list of str).
    """
    return {
        "success": True,
        "message": "norirobotics-mcp: 4 tools, session-gated motion/recording.",
        "tools": [
            {
                "name": "nori_info",
                "purpose": "Specs, SDK links, XLeRobot lineage, HN community reaction, actuator-upgrade notes, fleet peers. No session required.",
            },
            {
                "name": "nori_session",
                "purpose": "connect / disconnect / status / wait_ready. Real robot when NORI_MCP_SUPABASE_* is set, else nori_sdk mock_session().",
            },
            {
                "name": "nori_control",
                "purpose": "jog / set_jog / clear_jog / action / pose (motion) + estop / estop_confirmed / reset_latch / reset_arm (safety). Requires an open session.",
            },
            {
                "name": "nori_recording",
                "purpose": "start / stop / snapshot / frames / set_bitrate / set_paused — LeRobot-format episode capture. Requires an open session.",
            },
        ],
        "typical_flow": [
            "nori_info(operation='info')  # optional — orient yourself",
            "nori_session(operation='connect')",
            "nori_session(operation='wait_ready')",
            "nori_control(operation='action', targets={...})",
            "nori_recording(operation='episode_start', task='pour water into cup')",
            "nori_recording(operation='episode_stop')",
            "nori_session(operation='disconnect')",
        ],
    }


@mcp.tool()
async def nori_shutdown() -> dict[str, Any]:
    """NORI_SHUTDOWN — close the active Nori session (if any) and confirm clean teardown.

    Does not terminate the MCP server process itself — only releases the robot/mock session so
    a subsequent nori_session(operation='connect') starts clean.

    Returns:
        success (bool), message (str), was_connected (bool).
    """
    was_connected = await session_state.disconnect()
    return {
        "success": True,
        "message": "Session closed." if was_connected else "No active session was open.",
        "was_connected": was_connected,
    }
