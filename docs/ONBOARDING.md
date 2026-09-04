# Onboarding — Nori A3

This MCP server started life controlling **a physical robot that didn't exist in this household
yet** (Nori A3 is preorder-only, $1,688, shipping Fall 2026). That's no longer the only real A3
in the picture — this repo's own maintainer emailed Nori Robotics' founder with a link to it, and
he has a live A3 running in his office. So "onboarding" now means two things: understanding the
mock-vs-real posture, and registering whichever real robots you actually have access to as named
**profiles** — not a single env-var-driven identity.

## Physical vs. Virtual Twin — always explicit

Every `nori_session`/`nori_recording` response carries `robot_kind` (`"physical"` or
`"virtual"`) and `profile_name`. Never infer real-vs-mock from anything else — a training
pipeline or a person reading a recorded episode needs a direct answer, not an inference from
whether some env var happened to be set.

## What you need (today, zero configuration)

- `nori_info` (specs/SDK/lineage/community) — no session required.
- `nori_session(operation="connect")` — works out of the box against the built-in **Virtual
  Twin** profile (`nori_sdk.mock.mock_session()`, the SDK's own upstream-supported mock). The
  full test suite runs against this.

## Registering a physical A3

Any physical A3 you have Supabase credentials for — your own unit once it ships, or someone
else's (e.g. a demo unit, a colleague's office robot) if they've shared access — becomes a named
profile via `nori_session(operation="add_profile", ...)` or the webapp's Session page:

```python
nori_session(
    operation="add_profile",
    name="Mr. Li's A3",  # or whatever's meaningful to you
    kind="physical",
    supabase_url="https://xxxx.supabase.co",
    supabase_anon_key="...",
    robot_room="NORI-A3-0001",  # from Nori Lab
    user_email="you@example.com",  # optional, for UserAuth token refresh
    user_password="...",  # optional
)
```

This performs a real `wait_ready()` round-trip (up to 15s) before saving — bad credentials are
rejected outright, not silently stored as a broken profile. You can register more than one
physical A3 this way; `nori_session(operation="list_profiles")` shows everything saved, and
`nori_session(operation="switch_profile", profile_id=...)` picks which one future `connect()`
calls use.

**Legacy `.env` path still works.** If `NORI_MCP_SUPABASE_URL` / `NORI_MCP_SUPABASE_ANON_KEY` /
`NORI_MCP_ROBOT_ROOM` are set in `.env` (copied from `.env.example`), they're auto-migrated into
a named physical profile the first time the server starts — no forced re-onboarding for anyone
already using the old single-robot env-var flow.

Pass `force_mock=true` to any `connect` call to test against the Virtual Twin even with a
physical profile active or selected — the response still honestly reports `robot_kind: "virtual"`
in that case, never the bypassed physical profile's identity.

## Bring-up checklist (once you have real credentials for a unit)

1. Power on the A3, confirm it's paired in Nori Lab and shows "online."
2. `nori_session(operation="add_profile", kind="physical", ...)` with its Supabase URL/anon
   key/robot_room — this both registers and live-verifies the connection.
3. `nori_session(operation="switch_profile", profile_id=...)` to make it the active profile.
4. `nori_session(operation="connect")` → confirm `robot_kind: "physical"` in the response.
5. `nori_session(operation="wait_ready")` → confirm you get back a real `RobotInfo`, not the
   mock's synthetic one.
6. Before any motion: check battery via `nori_session(operation="status")` telemetry, and clear
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
- `robot_kind: "virtual"` in a `nori_session` response is expected and correct until you've
  registered a physical profile — it is not a bug or a sign of misconfiguration.

## Reference docs

- `docs/ARCHITECTURE.md` — session model, mock-vs-real decision point
- `docs/WRAPPEE.md` — what Nori A3 / nori-sdk is, lineage, community
- [`mcp-central-docs/projects/norirobotics-mcp/RESEARCH.md`](https://github.com/sandraschi/mcp-central-docs/blob/main/projects/norirobotics-mcp/RESEARCH.md) — full sourced research pass
