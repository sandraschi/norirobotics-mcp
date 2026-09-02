"""Static Nori A3 reference data — specs, lineage, community reaction, fleet map.

Sourced from mcp-central-docs/projects/norirobotics-mcp/RESEARCH.md (2026-09-02 pass).
Keep this in sync if Nori Robotics revises published specs before Fall 2026 shipment.
"""

from __future__ import annotations

from typing import Any

NORI_HERO: dict[str, Any] = {
    "product": "Nori A3",
    "vendor": "Nori Robotics (YC S26, San Francisco)",
    "tagline": "Affordable bimanual mobile manipulator, built for people who want to actually build with one.",
    "price_usd": 1688,
    "ships": "Fall 2026 (second batch, no deposit)",
    "specs": {
        "dof": 19,
        "arms": "2x 7+1 DOF, 55cm reach, 1.5kg payload per arm",
        "lift": "3-stage telescoping steel column, 69-145cm, 76cm travel @ 30mm/s",
        "base": "Differential drive + passive casters, 45x45cm footprint",
        "weight_kg": 20.4,
        "actuators": "Feetech STS-series bus servos (STS3095/STS3250/STS3215), torque-graded per joint",
        "gripper": "Soft TPU fingers, sensorless force sensing via servo Present_Current register",
        "compute": "Raspberry Pi 5, 4GB RAM (bus I/O + control loop only; policy inference off-board)",
        "cameras": "4x 720p RGB @ 30fps (grippers x2, head, neck)",
        "lidar": "2D, 12m range, 8-12Hz scan, 0.72deg angular resolution @ 10Hz",
        "audio": "Dual microphone array (full-duplex), onboard speaker",
        "battery": "432Wh, 6-8h operation",
    },
    "sources": [
        "https://www.norirobotics.com/",
        "https://arxiv.org/html/2605.16537",
        "https://news.ycombinator.com/item?id=49525153",
    ],
}

SDK_LINKS: dict[str, Any] = {
    "sdk_repo": "https://github.com/Nori-Robotics/nori-sdk-py",
    "pypi": "nori-sdk (v1.1.0 as of this research pass; extras: all, webrtc, supabase, dev)",
    "protocol": "nori-protocol over WebRTC data channel, Supabase Realtime signaling — no serial/USB",
    "lab_app": "https://lab.norirobotics.com/",
    "dataset_format": "LeRobot-compatible — existing Hugging Face LeRobot training pipelines apply without conversion",
    "policies": "ACT-style and VLA policies, trained off-board (Pi 5 does not run inference)",
    "license": "Apache-2.0 (SDK). The robot as a whole is NOT open-sourced; the actuator-protection layer is.",
}

PREDECESSOR: dict[str, Any] = {
    "summary": (
        "Prior team version ran on the XLeRobot base. Per the A3 paper: 'A3 shares none of that hardware' — "
        "clean-sheet redesign, but the lift, actuator-protection stack, and sensorless force channel carry forward."
    ),
    "xlerobot": {
        "description": (
            "Fully open-source dual-arm mobile robot: SO-100/SO-101 arms (TheRobotStudio/SO-ARM100) + "
            "Lekiwi omnidirectional base + IKEA RASKOG cart chassis. ~$660 BOM, 90% 3D-printed, "
            "~67min assembly. Built directly on the Hugging Face LeRobot ecosystem."
        ),
        "community": "4.8k+ GitHub stars, 6,000+ builder community (research-pass snapshot, re-verify before quoting live)",
        "links": [
            "https://xlerobot.readthedocs.io/en/latest/index.html",
            "https://github.com/TheRobotStudio/SO-ARM100",
        ],
    },
    "hf_parentage_note": (
        "No confirmed Nori Robotics org/dataset presence on huggingface.co found in this research pass. "
        "LeRobot compatibility is protocol-level (dataset schema + ACT/VLA pipeline reuse) via the XLeRobot/"
        "SO-101 lineage, not evidence of a direct Nori<->HF publishing relationship. Re-verify before stating "
        "a formal HF partnership exists."
    ),
}

COMMUNITY_REACTION: dict[str, Any] = {
    "source": "Launch HN: Nori Robotics (YC S26) — 97 points, 36 comments",
    "url": "https://news.ycombinator.com/item?id=49525153",
    "praise": [
        "Price point genuinely disruptive for hobbyists/researchers",
        "Wheeled (not bipedal) form factor read as safer for home use than Unitree G1-class bipeds",
        "Open SDK + 3D-printable/replaceable parts",
    ],
    "criticism": [
        "RC-style bus servos flagged as the precision ceiling vs. QDD actuators (CubeMars, MyActuator named)",
        "Demoed tasks (e.g. clothes folding) read by some as staged / closer to 'throwing into a pile'",
        "Category-level skepticism: home robotics 'not interesting for another 5-10 years' per several commenters",
        "Business-model skepticism vs. low-cost Chinese humanoid suppliers; K-Scale Labs shutdown cited as precedent",
        "Pricing skepticism: one commenter argued ~$20k would better reflect a robust research platform",
        "Privacy/telemetry questions given cloud-mediated WebRTC + Supabase control channel for an in-home robot",
    ],
    "read": (
        "HN's real disagreement isn't whether the hardware works roughly as specced — it's whether RC servos "
        "+ cloud-mediated WebRTC control are the right foundation for a manipulation robot."
    ),
}

ACTUATOR_UPGRADE_NOTES: dict[str, Any] = {
    "summary": (
        "Feetech is already a Shenzhen manufacturer (Shenzhen Feite Model Co.) — the real ask from the HN "
        "thread isn't geography, it's actuator CLASS: swapping RC-style position-only bus servos for "
        "quasi-direct-drive (QDD) / integrated BLDC actuators with true current/torque sensing and higher "
        "control bandwidth."
    ),
    "candidates_named_on_hn": [
        {
            "vendor": "CubeMars",
            "note": "AK-series QDD actuators, Suzhou-based, common in open humanoid/quadruped builds",
        },
        {"vendor": "MyActuator", "note": "RMD-series integrated BLDC, Suzhou-based, common in open biped/arm projects"},
    ],
    "most_plausible_target": (
        "Shoulder/lift axes, where STS3095's 95kg-cm ceiling is closest to being load-limited. Nori's own "
        "actuator-protection layer is already open-sourced and torque/stall-agnostic at the protocol level, "
        "which is what would make a QDD swap tractable without redesigning the whole safety stack."
    ),
    "caveat": (
        "No specific BOM/part-number recommendation is made here — needs a real torque/backdrivability "
        "comparison pass before it becomes fleet advice, not just an 'HN mentioned this' note. "
        "See universal-actuator-mcp for where that abstraction belongs."
    ),
}

FLEET_PEERS: list[dict[str, str]] = [
    {
        "id": "robotics-mcp",
        "note": "Fleet hub for physical + virtual robots — norirobotics-mcp registers here as a member.",
    },
    {
        "id": "teleoperator-mcp",
        "note": "WebXR teleop gateway (Pico 4 / Quest). Nori's own control path is WebRTC remote-teleop — natural pairing for VR-driven demonstration collection.",
    },
    {
        "id": "vla-mcp",
        "note": "Logged as Alpha/Shelfware — never used in production. Nori LeRobot-format recordings are its first plausible real workload.",
    },
    {
        "id": "universal-actuator-mcp",
        "note": "Motor/actuator abstraction layer — home for future Feetech-to-QDD actuator-upgrade tooling.",
    },
    {
        "id": "bumi-mcp",
        "note": "Closest structural precedent: wheeled consumer robot, specs+OSS-info tools now, physical control gated behind a verified bridge.",
    },
]
