[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.4-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

# norirobotics-mcp

Control the [Nori Robotics A3](https://www.norirobotics.com/) — a $1,688, 19-DOF wheeled
bimanual home robot — from Claude, with a webapp dashboard for status and teleop.

## What this wraps

Wraps [`nori-sdk`](https://github.com/Nori-Robotics/nori-sdk-py) (Apache-2.0), Nori Robotics'
official Python client. The SDK talks to the robot over a **WebRTC data channel** with
**Supabase Realtime signaling** — there is no serial/USB/ROS bridge to fake. See
[docs/WRAPPEE.md](docs/WRAPPEE.md) for what Nori A3 is, its XLeRobot/Hugging Face LeRobot
lineage, and where its community lives.

**No physical A3 exists in this household yet — the robot ships Fall 2026.** Every
session-gated tool defaults to `nori_sdk`'s own upstream-supported `mock_session()` until real
Supabase credentials are configured. This is the SDK's declared mock, not a fleet-invented fake
— see [docs/ONBOARDING.md](docs/ONBOARDING.md).

## What You Can Do

**How it runs**: headless FastMCP server (stdio or HTTP) that opens one WebRTC session against
either a real A3 (Supabase credentials configured) or `nori_sdk.mock.mock_session()`. Nori
Robotics' own `lab.norirobotics.com` webapp is never bundled or replaced — this dashboard is a
narrower, agent-oriented view (session status, tool calls, recording state).

| Direction | Artifacts | Notes |
|-----------|-----------|-------|
| **Hands-in** | joint/gripper targets, Cartesian poses, jog payloads, episode task labels | Via MCP tool params or the webapp Control/Recording pages |
| **Hands-out** | robot telemetry/status/camera_layout, LeRobot-format episode recordings, video snapshots | `nori_session`, `nori_recording` |

- Specs, SDK links, XLeRobot/HF LeRobot lineage, and Hacker News launch-thread reaction — no session required (`nori_info`)
- Open/close/inspect a live control session, real or mock (`nori_session`)
- Jog, move-to-target, Cartesian pose control, e-stop and fault reset (`nori_control`)
- Start/stop episode recording in LeRobot-compatible format, video snapshot/bitrate control (`nori_recording`)
- Fleet-aware: registers with `robotics-mcp`, pairs naturally with `teleoperator-mcp` for VR-driven
  demonstration collection, and feeds `vla-mcp`'s LeRobot training pipeline

## Quick Install

```bash
git clone https://github.com/sandraschi/norirobotics-mcp
cd norirobotics-mcp
uv sync
uv run norirobotics-mcp
```

See [INSTALL.md](INSTALL.md) for the drag-and-drop `.mcpb` path and full options.

## Example Prompts

- "What are the Nori A3's specs, and what did Hacker News say about it at launch?"
- "Open a Nori session and check the current telemetry."
- "Start an episode recording for pouring water into a cup, then stop it after I confirm."

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Onboarding](docs/ONBOARDING.md) | Mock-vs-real session, Supabase credentials, pre-hardware posture |
| [Wrapped SDK](docs/WRAPPEE.md) | What Nori A3 / nori-sdk is, lineage, community, disambiguation |
| [Architecture](docs/ARCHITECTURE.md) | Session model, ports, data flow |
| [Configuration](docs/CONFIGURATION.md) | Env vars, config options |
| [Tool Reference](docs/TOOLS.md) | All 6 MCP tools |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## Requirements

Python 3.11+, Claude Desktop (or any MCP client). No physical robot required for development —
`nori_sdk`'s mock session covers the full API surface.

## License

MIT
