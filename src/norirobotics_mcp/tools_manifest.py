"""Static MCP tool catalog for the webapp Tools page / fleet discovery."""

from __future__ import annotations

from typing import Any

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "nori_info",
        "description": "Specs, SDK links, XLeRobot lineage, HN community reaction, actuator-upgrade notes, fleet peers. No session required.",
        "params": {"operation": "info|specs|sdk_links|predecessor|community|actuator_upgrade|fleet_peers"},
    },
    {
        "name": "nori_session",
        "description": "Open/close/inspect the live Nori A3 control session (real or nori_sdk mock).",
        "params": {"operation": "connect|disconnect|status|wait_ready", "force_mock": "bool"},
    },
    {
        "name": "nori_control",
        "description": "Motion (jog/set_jog/action/pose) + safety (estop/reset). Requires an open session.",
        "params": {"operation": "str", "payload": "dict", "targets": "dict", "side": "str"},
    },
    {
        "name": "nori_recording",
        "description": "LeRobot-format episode/session recording (nori_sdk RecordVerb), video snapshot/bitrate. Requires an open session.",
        "params": {
            "operation": "session_start|episode_start|episode_stop|episode_discard|session_end|session_discard|start|stop|discard|discard_last|status|snapshot|frames|set_bitrate|set_paused"
        },
    },
    {"name": "nori_help", "description": "Tool reference + typical call order.", "params": {}},
    {"name": "nori_shutdown", "description": "Close the active session without stopping the server.", "params": {}},
]
