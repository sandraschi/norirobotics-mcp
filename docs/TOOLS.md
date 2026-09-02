# Tool Reference

norirobotics-mcp ships **6 tools**: 4 portmanteaus + `nori_help` + `nori_shutdown`.

## `nori_info(operation, ...)`

No session required. Static reference data.

| Operation | Returns |
|---|---|
| `info` (default) | Tagline, vendor, price, ship date, spec summary |
| `specs` | Full structured spec sheet |
| `sdk_links` | nori-sdk-py repo, PyPI package, protocol, dataset format, license |
| `predecessor` | XLeRobot lineage, what carried forward to the A3 |
| `community` | Hacker News launch-thread praise/criticism |
| `actuator_upgrade` | RC-servo-vs-QDD actuator upgrade note (CubeMars/MyActuator, no fabricated BOM) |
| `fleet_peers` | Related fleet MCPs (`robotics-mcp`, `teleoperator-mcp`, `vla-mcp`, `universal-actuator-mcp`, `bumi-mcp`) |

## `nori_session(operation, force_mock=False)`

| Operation | Effect |
|---|---|
| `connect` | Open a session — real if `NORI_MCP_SUPABASE_*` set, else `nori_sdk.mock.mock_session()`. Idempotent. |
| `disconnect` | Close the active session. No-op if already closed. |
| `status` (default) | Connection state, mock/real flag, telemetry/status/daemon_status/camera_layout if connected. |
| `wait_ready` | Block until the robot reports ready; returns `RobotInfo`. |

## `nori_control(operation, ...)`

Requires an open session. Motion ops: `jog`, `set_jog`, `clear_jog`, `action`, `pose`. Safety
ops: `estop`, `estop_confirmed`, `reset_latch`, `reset_arm`.

| Operation | Key args |
|---|---|
| `jog` | `payload` (dict), `duration` (float, seconds) |
| `set_jog` | `payload` (dict) — continuous until cleared |
| `clear_jog` | *(none)* |
| `action` | `targets` (dict), `wait` (bool) |
| `pose` | `side` ("left"\|"right"), `position_m` ([x,y,z]), `orientation_xyzw` (optional), `wait` |
| `estop` | *(none)* |
| `estop_confirmed` | `timeout` (float) |
| `reset_latch` | *(none)* |
| `reset_arm` | `arm` ("left"\|"right") |

## `nori_recording(operation, ...)`

Requires an open session. `operation` maps 1:1 onto nori_sdk's own `RecordVerb` literal — not a
fleet-invented "start/stop a named task" abstraction. Episodes persist server-side in
LeRobot-compatible format.

| Operation | Key args | Effect |
|---|---|---|
| `session_start` | | Open a capture session (does not itself start recording) |
| `episode_start` | `task` (str) | Begin recording one episode within the open session |
| `episode_stop` | | End the current episode recording |
| `episode_discard` | | Discard the current (unfinished) episode |
| `session_end` | | Close the session, keeping recorded episodes |
| `session_discard` | | Close the session, discarding all its episodes |
| `start` | `task` (str) | Simpler top-level equivalent — opens a session and arms recording |
| `stop` | | Stop whatever is currently active |
| `discard` | | Discard whatever is currently active |
| `discard_last` | | Discard the most recently completed episode |
| `status` (default) | | Current `RecordState`: `recording`, `session_open`, `episodes_kept`, `free_gb` |
| `snapshot` | `role`, `track_timeout` | Grab a still frame. Mock session has no video track — set a short `track_timeout` for fast negative tests |
| `frames` | | Returns `camera_layout` (bounded, not a video stream) |
| `set_bitrate` | `kbps` (int) | Adjust live video bitrate |
| `set_paused` | `paused` (bool) | Pause/resume the live video stream |

Verified against the installed `nori_sdk` package: `episode_start` actually flips `recording`
to `true`; plain `start` opens a session but does not by itself set `recording=true`.

## `nori_help()`

Quick reference: tool list + typical call order. No args.

## `nori_shutdown()`

Closes the active session (real or mock) without terminating the MCP server process. No args.
