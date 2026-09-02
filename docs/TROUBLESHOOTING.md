# Troubleshooting

## `nori_session(operation="connect")` always returns `mock: true`
**Cause**: One or more of `NORI_MCP_SUPABASE_URL`, `NORI_MCP_SUPABASE_ANON_KEY`,
`NORI_MCP_ROBOT_ROOM` is unset.
**Fix**: This is expected pre-hardware (A3 ships Fall 2026). Set all three (plus
`NORI_MCP_USER_EMAIL` / `NORI_MCP_USER_PASSWORD`) once you have a unit — see `docs/ONBOARDING.md`.

## `nori_control` / `nori_recording` return "No active session"
**Cause**: Called before `nori_session(operation="connect")`.
**Fix**: Every motion/safety/recording op requires an open session first — see `nori_help()`
for the typical call order.

## `ImportError` on `aiortc` or `av` when connecting to a real robot
**Cause**: Base `pip install nori-sdk` is "protocol only, zero dependencies" — WebRTC transport
needs the `[all]` or `[webrtc]` extra.
**Fix**: This repo already depends on `nori-sdk[all]>=1.1.0` in `pyproject.toml` — re-run
`uv sync`. If you vendored a different install, add the extra explicitly.

## Server doesn't appear in Claude Desktop
**Cause**: Config JSON is malformed.
**Fix**: Validate at jsonlint.com, check for trailing commas.

## "command not found: uv"
**Cause**: uv not installed or not in PATH.
**Fix**: `winget install astral-sh.uv` then restart terminal.

## `estop_confirmed` times out
**Cause**: Expected on the mock backend for some `MockRobot` configurations
(`accepted=False`, `online=False`) — the mock is deliberately configurable to exercise failure
paths. Against a real robot, a timeout means the confirmation never reached the control channel
— check the WebRTC connection state via `nori_session(operation="status")` first.
