# Onboarding — Nori A3

This MCP server controls a **physical robot that does not exist in this household yet**. Nori
A3 is preorder-only (second batch, $1,688, no deposit), shipping **Fall 2026**. Onboarding here
means understanding the mock-vs-real posture, not bringing hardware up.

## What you need (today)

- Nothing. `nori_info` (specs/SDK/lineage/community) works with zero configuration.
- `nori_session(operation="connect")` works with zero configuration too — it falls back to
  `nori_sdk.mock.mock_session()`, the SDK's own upstream-supported mock robot. All 24 tests in
  this repo run against that mock.

## What you'll need once a unit ships

- A Nori A3 unit, powered on and paired to your Nori account (via `lab.norirobotics.com`).
- Supabase project URL + anon key (Nori Robotics provisions this per-account — not something you
  self-host).
- Your robot's `room` identifier (e.g. `NORI-A3-0001`), from Nori Lab.
- Your Nori account email/password (for `UserAuth` token refresh).

Set these in `.env` (copy from `.env.example`):

```
NORI_MCP_SUPABASE_URL=https://xxxx.supabase.co
NORI_MCP_SUPABASE_ANON_KEY=...
NORI_MCP_ROBOT_ROOM=NORI-A3-0001
NORI_MCP_USER_EMAIL=you@example.com
NORI_MCP_USER_PASSWORD=...
```

Once set, `nori_session(operation="connect")` opens a real WebRTC session instead of the mock —
no code changes needed, `session_state.py` picks real vs. mock based on whether credentials are
present. Pass `force_mock=true` to any `connect` call to keep testing against the mock even with
real credentials configured.

## Bring-up checklist (once you have a unit)

1. Power on the A3, confirm it's paired in Nori Lab and shows "online."
2. Set the four `NORI_MCP_SUPABASE_*` / `NORI_MCP_ROBOT_ROOM` env vars above.
3. `nori_session(operation="connect")` → confirm `mock: false` in the response.
4. `nori_session(operation="wait_ready")` → confirm you get back a real `RobotInfo`, not the
   mock's synthetic one.
5. Before any motion: check battery via `nori_session(operation="status")` telemetry, and clear
   the workspace — the A3's arms have 55cm reach and a 1.5kg payload per arm.

## Costs / notes

- No subscription cost for `norirobotics-mcp` itself. Nori Robotics' own account/Supabase
  provisioning terms are theirs, not documented here — check `lab.norirobotics.com`.
- The control channel is cloud-mediated (WebRTC + Supabase Realtime) — there's no local-only
  operation mode documented in the SDK as of this research pass. This was a live point of
  concern in the [Hacker News launch thread](https://news.ycombinator.com/item?id=49525153)
  (privacy/telemetry for an in-home robot) — worth re-checking Nori's docs before treating this
  as settled.

## Common pitfalls

- Don't assume `nori-sdk`'s base `pip install nori-sdk` gives you WebRTC — that install is
  "protocol only, zero dependencies." This repo depends on `nori-sdk[all]` (aiortc + av +
  websocket-client) specifically so real sessions work out of the box.
- `mock: true` in a `nori_session` response is expected and correct pre-hardware — it is not a
  bug or a sign of misconfiguration.

## Reference docs

- `docs/ARCHITECTURE.md` — session model, mock-vs-real decision point
- `docs/WRAPPEE.md` — what Nori A3 / nori-sdk is, lineage, community
- [`mcp-central-docs/projects/norirobotics-mcp/RESEARCH.md`](https://github.com/sandraschi/mcp-central-docs/blob/main/projects/norirobotics-mcp/RESEARCH.md) — full sourced research pass
