# Changelog

## [Unreleased] — 2026-09-02

### Added
- Initial scaffold: FastMCP 3.4 server wrapping `nori-sdk` (Apache-2.0, PyPI `nori-sdk` 1.1.0) —
  the real, verified WebRTC/Supabase Python client for the Nori Robotics A3.
- `nori_info`, `nori_session`, `nori_control`, `nori_recording`, `nori_help`, `nori_shutdown` tools.
- Session lifecycle defaults to `nori_sdk.mock.mock_session()` (upstream-declared mock) until
  `NORI_MCP_SUPABASE_*` credentials are configured — no unit exists in this household yet
  (A3 ships Fall 2026).
- REST API (`/api/health`, `/api/hero`, `/api/session/*`, `/api/control/*`, `/api/recording/*`,
  `/api/logs`, `/api/llm/*`) + React/Vite/Tailwind/Zustand webapp (Dashboard, Info, Session,
  Control, Recording, Settings, Help, Logging pages) on ports 11970/11971.
- 33 pytest cases run against the real installed `nori_sdk` package (mock backend), all green.
- Full docs stack, INSTALL, fleet registration (`robotics-mcp`, `WEBAPP_PORTS.md` 11970/11971).
- Research dossier: `mcp-central-docs/projects/norirobotics-mcp/RESEARCH.md` (specs, HN launch
  thread, XLeRobot/LeRobot lineage, actuator-upgrade notes).

### Fixed (found via live browser testing, not just unit tests)
- `nori_control`: `estop`, `set_jog`, `reset_latch`, `reset_arm` were incorrectly `await`ed —
  these are synchronous methods on `nori_sdk.RemoteTeleop`, not coroutines. Confirmed by
  introspecting the installed package; regression tests added.
- `nori_recording`: replaced an invented "start/stop a task by verb name" API with nori_sdk's
  actual `RecordVerb` literal (`session_start`/`episode_start`/`episode_stop`/.../`status`) —
  the original design silently didn't match how the SDK distinguishes a capture *session* from
  an *episode* within it. `set_video_bitrate`/`set_video_paused` were also incorrectly awaited
  (sync methods).
- `nori_recording(operation="snapshot")`: added a `track_timeout` param — the mock session has
  no video track by default, so `snapshot()` genuinely times out (20s) against it; tests now use
  a short timeout to assert the honest failure fast instead of hanging.
