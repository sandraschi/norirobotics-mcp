"""Static MCP tool catalog for the webapp Tools page / fleet discovery."""

from __future__ import annotations

from typing import Any

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "nori_info",
        "description": "Specs, SDK links, XLeRobot lineage, HN community reaction, actuator-upgrade notes, fleet peers. No session required.",
        "params": {
            "operation": "info|specs|sdk_links|predecessor|community|actuator_upgrade|fleet_peers|skills_marketplace"
        },
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
        "description": "Motion (jog/set_jog/action/pose) + safety (estop/reset) + policy/leader streaming "
        "(policy_stream/policy_stream_status/set_leader_action). Requires an open session.",
        "params": {
            "operation": "str",
            "payload": "dict",
            "targets": "dict",
            "side": "str",
            "policy_action": "start|stop|status",
            "extra": "dict",
        },
    },
    {
        "name": "nori_navigation",
        "description": "Named waypoint navigation (nori-sdk 1.1.0): remember/delete/list/navigate_to a "
        "saved destination, goto_pose, cancel/await a Nav2 goal. Requires an open session.",
        "params": {
            "operation": "remember_waypoint|delete_waypoint|list_waypoints|navigate_to_waypoint|goto_pose|cancel_navigation|await_navigation|status",
            "name": "str",
            "side": "str",
            "position_m": "list[float]",
            "goal_id": "str",
        },
    },
    {
        "name": "nori_perception",
        "description": "Opt-in LiDAR/IMU/vision-stack reads (nori-sdk 1.1.0). Requires an open session. "
        "lidar_scan/imu_sample/perceive return null until configure_sensor_streams enables the feed "
        "and a real robot is publishing.",
        "params": {
            "operation": "lidar_scan|imu_sample|perceive|configure_sensor_streams|status",
            "lidar_hz": "float",
            "imu_hz": "float",
            "lidar_max_points": "int",
        },
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
