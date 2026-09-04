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

## `nori_session(operation, ...)`

Also owns the multi-bot profile registry — "physical A3 vs. Virtual Twin" is an explicit,
named-profile choice, not an env-var side effect. See `docs/ONBOARDING.md` for the full flow.

| Operation | Key args | Effect |
|---|---|---|
| `connect` | `profile_id`, `force_mock` | Open a session against the given (or active) profile. Real WebRTC/Supabase if the profile is `kind="physical"`, else `nori_sdk.mock.mock_session()`. Idempotent. `force_mock=true` bypasses a physical profile without disturbing which one is active. |
| `disconnect` | | Close the active session. No-op if already closed. |
| `status` (default) | | Connection state, `robot_kind`/`profile_name` (always present, even when disconnected — reflects what a `connect` would use), telemetry/status/daemon_status/camera_layout if connected. |
| `wait_ready` | | Block until the robot reports ready; returns `RobotInfo`. |
| `list_profiles` | | Every saved robot profile plus which one is active. |
| `add_profile` | `name`, `kind`, plus (for `kind="physical"`) `supabase_url`, `supabase_anon_key`, `robot_room`, `user_email`, `user_password` | Save a new profile. Physical credentials are live-tested (a real `wait_ready()` round-trip, up to 15s) before saving — bad credentials are rejected, never silently stored. |
| `switch_profile` | `profile_id` | Set which profile future `connect()` calls default to. Does not reconnect an already-open session. |
| `remove_profile` | `profile_id` | Delete a saved profile. Refuses to remove the active profile or the built-in `virtual` profile. |

Every response — from `nori_session` and `nori_recording` alike — carries `robot_kind`
(`"physical"` or `"virtual"`) and `profile_name`. Check these before treating a recorded episode
as real-hardware data; nothing else in the response shape guarantees that distinction.

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

Every response carries `robot_kind`/`profile_name` from the connected session's profile — check
these before trusting an episode as real-hardware data. Note: `nori_sdk`'s own `record()` call has
no metadata hook to embed this into the on-disk LeRobot dataset itself (verified against the
installed SDK signature) — the provenance fields are guaranteed on the MCP response only.

## `nori_help()`

Quick reference: tool list + typical call order. No args.

## `nori_shutdown()`

Closes the active session (real or mock) without terminating the MCP server process. No args.
