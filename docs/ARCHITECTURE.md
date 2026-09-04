# Architecture

## Overview

```
Claude / MCP client
        |
        v  MCP (stdio or HTTP :11970/mcp)
+-------------------------+
|     norirobotics-mcp    |
|  nori_info               (static knowledge, no session)
|  nori_session             connect/disconnect/status/wait_ready
|  nori_control              jog/set_jog/action/pose/estop/reset_*
|  nori_recording             record/snapshot/frames/bitrate/pause
+-------------------------+
        |
        v  robot_profiles.py picks a named profile ("Virtual Twin" default, or
        v  any registered physical A3) -->
        v  nori_sdk.RemoteTeleop  (kind="physical")   OR   nori_sdk.mock.mock_session()  (kind="virtual")
+-------------------------+
|  WebRTC data channel     |          no hardware -> in-process MockRobot,
|  + Supabase Realtime     |          same API surface, zero network calls
|  signaling                |
+-------------------------+
        |
        v  (real only)
   Nori A3 robot (Raspberry Pi 5 onboard, Feetech bus servos,
   4x 720p cameras, 2D LiDAR, 432Wh battery)
```

## Session model (the one thing to understand)

`src/norirobotics_mcp/session_state.py` holds exactly **one** process-wide session — this
matches `nori-sdk`'s own model (one robot, one operator control channel). `nori_session(
operation="connect")` is idempotent: if a session is already open, it's reused rather than
re-opened.

Which backend `connect` picks is a **named-profile choice**, not a bare env-var check —
`src/norirobotics_mcp/robot_profiles.py`'s `RobotProfileStore` holds any number of profiles
(always at least the built-in `virtual` one), each explicitly `kind="physical"` or
`kind="virtual"`. This exists because a physical A3 is no longer hypothetical or singular: this
repo's own maintainer has a live A3 accessible in someone else's office, distinct from any unit
she owns herself, so "the one physical robot" stopped being a safe assumption.

| Condition | Backend |
|---|---|
| `connect(profile_id=...)` (or the store's active profile) resolves to a `kind="physical"` profile, `force_mock` not passed | Real `nori_sdk.RemoteTeleop` over WebRTC/Supabase, using *that profile's* credentials |
| Profile is `kind="virtual"`, or `force_mock=true` overrides a physical selection | `nori_sdk.mock.mock_session()` |

This is the **only** branch point in the codebase between mock and real — every tool
(`nori_control`, `nori_recording`) calls the same session object regardless of backend, because
`MockRobot` implements the same method surface as the real `RemoteTeleop` session. Which profile
actually backed a given session is never left implicit: `session_state.current_profile()` /
`current_profile_or_pending()` back a `robot_kind`/`profile_name` pair stamped onto every
`nori_session`/`nori_recording` response (`robot_profiles.provenance_fields()`) — the legacy
single-set-of-env-vars flow still works (auto-migrated into a named physical profile on first
run), but the ambiguity of "is `mock: true` because nothing's configured, or because something's
broken" is gone.

## Why no local/serial bridge exists

Unlike `bumi-mcp` or `yahboom-mcp` (which bridge to a local ROS 2 / rosbridge endpoint on the
robot's own SBC over the LAN), Nori A3's control path is cloud-mediated by design — `nori-sdk`
has no serial/USB/local-network transport documented. Do not add one; it would not match how
the actual robot works.

## Ports

| Port | Service |
|---|---|
| 11970 | Backend — FastAPI + FastMCP HTTP `/mcp` + REST `/api/*` |
| 11971 | Frontend — Vite React dashboard (`web_sota/`); proxies `/api` + `/mcp` → 11970 |

Registered in `mcp-central-docs/operations/WEBAPP_PORTS.md`.

## Data flow: recording → training

`nori_recording(operation="start", verb=..., task=...)` starts an episode recording that
`nori-sdk` persists server-side (Nori's backend) in **LeRobot-compatible** format. That's the
same dataset schema Hugging Face's `lerobot` training pipelines (ACT, VLA/SmolVLA, etc.) consume
directly — this is the intended handoff point into `vla-mcp` for anyone training policies from
collected demonstrations.
