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

## Part of the sandraschi Robotics + VR Fleet

norirobotics-mcp is one member of a larger set of MCP servers under the
[sandraschi](https://github.com/sandraschi) account that work together rather than in
isolation — a physical robot integration is far more useful with a virtual-first testing
path and a shared control hub than as a standalone wrapper. This is deliberately not a solo
project; it's built to the same portmanteau-tool, live-verified, honest-mock-vs-real
conventions the whole fleet follows, and it's designed to plug straight into it.

**Robotics fleet peers** (declared in `nori_info(operation="fleet_peers")` / `GET /api/hero`,
and reciprocally, norirobotics-mcp is registered as a member robot inside `robotics-mcp`
itself — see that repo's `robotics.nori_a3` config block and `NoriMcpClient` HTTP bridge):

| Repo | Role |
|------|------|
| [robotics-mcp](https://github.com/sandraschi/robotics-mcp) | Fleet hub for physical + virtual robots — one unified `robot_control` interface across Dreame vacuums, Yahboom ROSMASTER, Unitree quadrupeds, drones, and Nori A3, plus virtual robot ("vbot") spawning into the VR platforms below. norirobotics-mcp registers here as a member robot, bridged via HTTP rather than reimplemented — see `robot_control(robot_id="nori_a3", action=...)`. |
| [teleoperator-mcp](https://github.com/sandraschi/teleoperator-mcp) | WebXR teleop gateway (Pico 4 / Quest). Nori A3's own control path is WebRTC remote-teleop — a natural pairing for VR-driven demonstration collection: teleoperate in VR, record the episode through this server. |
| [vla-mcp](https://github.com/sandraschi/vla-mcp) | Vision-language-action training pipeline. Currently alpha/shelfware fleet-wide — Nori A3's LeRobot-format episode recordings (`nori_recording`) are its first plausible real workload rather than a synthetic one. |
| [universal-actuator-mcp](https://github.com/sandraschi/universal-actuator-mcp) | Motor/actuator abstraction layer — the eventual home for Feetech-to-QDD actuator-upgrade tooling, a real gap the Hacker News launch thread flagged for the A3's RC-servo arms (see `nori_info(operation="actuator_upgrade")` for the sourced, no-specific-recommendation-yet note). |
| [bumi-mcp](https://github.com/sandraschi/bumi-mcp) | Closest structural precedent in the fleet: another wheeled consumer robot, specs+OSS-info tools shipped first, physical control gated behind a verified bridge second — the same honest, staged rollout this repo follows. |

**VR crossconnects** (how a Nori A3 gets a virtual twin, via `robotics-mcp`'s
`robot_virtual`/`vbot_crud` tools — `platform="unity"` etc.):

| Repo | What it adds |
|------|---------------|
| [resonite-mcp](https://github.com/sandraschi/resonite-mcp) | Social VR platform control via ResoniteLink (real-protocol WebSocket, not OSC). Ships `resonite_link_spawn_fixture` for gripper/manipulation test fixtures (box/cup/ball/table/chair) and `resonite_link_animate` for spin/bob/real-physics-bounce — a natural staging ground for testing a Nori A3 pick-and-place task in VR before running it on hardware. |
| [overte-mcp](https://github.com/sandraschi/overte-mcp) | Open-source metaverse platform control, the source these fixture-spawner/animate/model-depot patterns were first built and live-verified against before being ported to the other VR repos. |
| [unity3d-mcp](https://github.com/sandraschi/unity3d-mcp) | Unity Editor automation via a live TCP bridge — `robotics-mcp`'s primary virtual-robot spawn target, now with the same fixture-spawner/animate capability (built from Unity's own native primitives, not a custom mesh generator). |
| [godot-mcp](https://github.com/sandraschi/godot-mcp) | Godot 4 engine control via TCP bridge — same fixture-spawner/animate pattern, plus a real model/texture asset depot with backup/restore. |
| [vrchat-mcp](https://github.com/sandraschi/vrchat-mcp) | VRChat integration - OSC avatar control plus REST (friends, users, notifications, real-time Pipeline events). VRChat's platform doesn't allow live external world-authoring the way the others do, so this one plugs in at the social/telepresence layer rather than the object-spawning one. |

The fixture-spawner/animate/depot capabilities listed above landed across all four world/engine
platforms in the same session (2026-09), each adapted to that platform's actual architecture —
same closed-form bounce physics ported four times, verified identical, not four independent
guesses. See each repo's own `CHANGELOG.md` for the live-verification details.

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
