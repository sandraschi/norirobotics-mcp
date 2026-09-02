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
        v  nori_sdk.RemoteTeleop  (real)   OR   nori_sdk.mock.mock_session()  (default)
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

Which backend `connect` picks:

| Condition | Backend |
|---|---|
| `NORI_MCP_SUPABASE_URL` + `NORI_MCP_SUPABASE_ANON_KEY` + `NORI_MCP_ROBOT_ROOM` all set, `force_mock` not passed | Real `nori_sdk.RemoteTeleop` over WebRTC/Supabase |
| Otherwise (default, pre-hardware) | `nori_sdk.mock.mock_session()` |

This is the **only** branch point in the codebase between mock and real — every tool
(`nori_control`, `nori_recording`) calls the same session object regardless of backend, because
`MockRobot` implements the same method surface as the real `RemoteTeleop` session.

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
