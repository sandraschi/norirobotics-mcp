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
        "description": "Open/close/inspect the live Nori A3 control session, and manage the multi-bot "
        "profile registry (Virtual Twin plus any number of named physical A3s).",
        "params": {
            "operation": "connect|disconnect|status|wait_ready|list_profiles|add_profile|switch_profile|remove_profile",
            "force_mock": "bool",
            "profile_id": "str",
            "name": "str",
            "kind": "physical|virtual",
            "supabase_url": "str",
            "supabase_anon_key": "str",
            "robot_room": "str",
            "user_email": "str",
            "user_password": "str",
        },
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
    {
        "name": "nori_vr",
        "description": "VR/physics twin: Unity/Overte/Godot/MuJoCo/Isaac spawn via other fleet repos (Unity real via model depot, MuJoCo local, Isaac USD).",
        "params": {"operation": "unity_spawn|unity_status|overte_spawn|godot_spawn|mujoco_view|isaac_export"},
    },
    {"name": "nori_help", "description": "Tool reference + typical call order.", "params": {}},
    {"name": "nori_shutdown", "description": "Close the active session without stopping the server.", "params": {}},
]
