"""FastMCP 3.4 — Nori Robotics A3 bimanual home robot MCP."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from norirobotics_mcp import session_state
from norirobotics_mcp.knowledge import FLEET_PEERS, NORI_HERO
from norirobotics_mcp.tool_control import nori_control
from norirobotics_mcp.tool_info import nori_info
from norirobotics_mcp.tool_recording import nori_recording
from norirobotics_mcp.tool_session import nori_session
from norirobotics_mcp.tool_vr import nori_vr

mcp = FastMCP(
    "norirobotics-mcp",
    instructions=(
        "Nori Robotics A3 (19-DOF wheeled bimanual home robot, ships Fall 2026): "
        "use nori_info(operation=...) for specs/SDK/lineage/community facts (no session needed), "
        "nori_session(operation='connect') to open a control session (real robot when "
        "NORI_MCP_SUPABASE_* env vars are set, otherwise nori_sdk's own mock_session()), "
        "then nori_control for motion/safety, nori_recording for LeRobot-format episode capture, "
        "and nori_vr for Unity/Overte/Godot/MuJoCo/Isaac spawning via other fleet repos. "
        "Always call nori_session(operation='connect') before nori_control/nori_recording."
    ),
)

# ── Prefab + annotated tool surface ───────────────────────────────────────

mcp.tool(
    annotations={"readOnlyHint": True, "openWorldHint": False},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
    app=True,
)(nori_info)

mcp.tool(
    annotations={"readOnlyHint": False, "openWorldHint": True},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
    app=True,
)(nori_session)

mcp.tool(
    annotations={"readOnlyHint": False, "openWorldHint": True, "destructiveHint": True},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
)(nori_control)

mcp.tool(
    annotations={"readOnlyHint": False, "openWorldHint": True},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
)(nori_recording)

mcp.tool(
    annotations={"readOnlyHint": False, "openWorldHint": True},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
    app=True,
)(nori_vr)


@mcp.tool(
    annotations={"readOnlyHint": True, "openWorldHint": False},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
    app=True,
)
async def nori_help() -> dict[str, Any]:
    """NORI_HELP — quick reference for norirobotics-mcp's five tools and typical call order.

    Returns:
        success (bool), message (str), tools (list of {name, purpose}), typical_flow (list of str).
    """
    return {
        "success": True,
        "message": "norirobotics-mcp: 5 tools, session-gated motion/recording + VR.",
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
            {
                "name": "nori_vr",
                "purpose": "unity_spawn/overte_spawn/godot_spawn/mujoco_view/isaac_export — VR/physics twin via other fleet repos (Unity/Overte/Godot/MuJoCo/Isaac).",
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


@mcp.tool(
    annotations={"readOnlyHint": False, "openWorldHint": False, "destructiveHint": True},
    output_schema={
        "type": "object",
        "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
        "required": ["success", "message"],
    },
)
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


# ── Resources & Prompts (SOTA) ────────────────────────────────────────────


@mcp.resource("nori://hero")
def hero_resource() -> dict[str, Any]:
    """Nori hero spec + fleet peers — for LLM context without tool call."""
    return {"hero": NORI_HERO, "fleet_peers": FLEET_PEERS}


@mcp.resource("nori://tools")
def tools_resource() -> dict[str, Any]:
    """Registered MCP tool manifest."""
    from norirobotics_mcp.tools_manifest import MCP_TOOLS

    return {"tools": MCP_TOOLS}


@mcp.prompt("nori-help")
def nori_help_prompt() -> str:
    """System prompt for Nori A3 — composes hero + tool order."""
    return (
        "You are a helpful assistant for the Nori Robotics A3 (19-DOF wheeled bimanual home robot, ships Fall 2026). "
        "Use nori_info for specs/community, nori_session(connect) to open a session (mock until Supabase creds set), "
        "then nori_control for motion/safety and nori_recording for LeRobot episode capture. "
        "Always call nori_session(connect) before motion/recording. Be precise, cite SDK lineage, and never invent a local serial API."
    )
