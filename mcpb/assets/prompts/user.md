# Using norirobotics-mcp — a practical guide

This guide is written for you, the person talking to Claude with this MCP server installed. It
walks through what the Nori Robotics A3 is, how the mock-vs-real distinction works day to day,
and gives worked example conversations for every tool so you know what to expect and what to ask
for. If you only read one section, read "The one thing to understand before anything else"
below — everything else follows from it.

## What you actually have installed

The Nori Robotics A3 is a $1,688, 19-degree-of-freedom wheeled bimanual home robot: two arms on
a mobile wheeled base, four onboard 720p cameras, a 2D LiDAR, a Raspberry Pi 5 brain, Feetech bus
servos, and a 432Wh battery. It descends from the open-source XLeRobot project and the Hugging
Face LeRobot ecosystem, and it ships with an official WebRTC teleoperation stack built by Nori
Robotics themselves. This MCP server, `norirobotics-mcp`, wraps that official stack — specifically
`nori-sdk`, Nori's own Apache-2.0-licensed Python client — so that Claude can open a session with
the robot, drive it, and record demonstrations, all through plain conversation rather than code
or a separate app. Nori Robotics also ships their own web dashboard at `lab.norirobotics.com`;
this MCP server does not replace or bundle that, it's a narrower, conversational layer on top of
the same underlying SDK.

## The one thing to understand before anything else

**If you don't yet own a physical A3, every tool still works — against a mock robot.** The A3
ships Fall 2026, and Nori Robotics' own SDK includes a full mock implementation,
`nori_sdk.mock.mock_session()`, that behaves like a real robot across the entire API surface: it
accepts motion commands, reports telemetry, records episodes, and responds to e-stops. This
server defaults to that mock automatically whenever real robot credentials aren't configured, so
you can explore every single tool today, safely, with nothing physical involved. When you do get
a real unit and configure it (see the Configuration section below), the exact same tool calls
start reaching actual hardware instead — nothing about how you talk to Claude changes, only what
answers on the other end. Ask Claude to check `nori_session(operation="status")` any time you
want to confirm which mode you're in; the response includes an explicit mock/real flag.

## Getting started: your first conversation

A good first exchange looks like this:

> **You**: "What is the Nori A3, and what did people think of it when it launched?"
>
> **Claude**: *(calls `nori_info(operation="info")` and `nori_info(operation="community")`)*
> "The A3 is a $1,688, 19-DOF wheeled bimanual home robot from Nori Robotics, descended from the
> XLeRobot project... On Hacker News, the launch thread was generally positive about the price
> point relative to comparable research platforms, with some skepticism about the RC-servo
> actuators' precision and longevity compared to quasi-direct-drive alternatives..."

This costs nothing and touches no session state — `nori_info` works with no robot connected at
all, real or mock, so it's always a safe way to start.

> **You**: "Okay, let's open a session and see what it reports."
>
> **Claude**: *(calls `nori_session(operation="connect")`, then `nori_session(operation=
> "status")`)* "Session opened — this is running against the mock robot, since no Supabase
> credentials are configured. Status reports: connected, idle, camera_layout shows 4 simulated
> feeds..."

Notice Claude should always tell you plainly whether you're on mock or real. If it doesn't, ask.

## Tool-by-tool walkthrough

### `nori_info` — everything you'd want to know before touching the robot

No session needed, always safe, always fast. Ask for:
- **`info`** (the default): a quick overview — tagline, vendor, price, ship date.
- **`specs`**: the full spec sheet — DOF count, arm reach, base details, camera/LiDAR
  configuration, weight, price.
- **`sdk_links`**: where the underlying SDK lives on GitHub and PyPI, what protocol it speaks,
  what dataset format it records into, and its license.
- **`predecessor`**: what the A3 inherited from the open-source XLeRobot project it descends
  from.
- **`community`**: an honest summary of the Hacker News launch-thread reaction — both what
  people liked and what they were skeptical of.
- **`actuator_upgrade`**: a candid discussion of the RC-servo vs. quasi-direct-drive actuator
  tradeoff, including what a CubeMars/MyActuator-based upgrade path might look like — explicitly
  without inventing a parts list, since nobody has actually built one.
- **`fleet_peers`**: the other MCP servers in this fleet that relate to Nori — `robotics-mcp`
  (multi-robot control hub), `teleoperator-mcp` (VR-driven demonstration collection),
  `vla-mcp` (training vision-language-action policies from your recordings),
  `universal-actuator-mcp`, and `bumi-mcp`.

Example:

> **You**: "Is there a plan to upgrade the actuators on this thing eventually?"
>
> **Claude**: *(calls `nori_info(operation="actuator_upgrade")`)* "There's no shipped upgrade
> path today — the A3 uses RC-servo actuators as-is. The honest tradeoff discussion is that
> quasi-direct-drive actuators (the kind CubeMars or MyActuator sell) would offer better force
> control and durability, but I don't have a real bill of materials or a built prototype to point
> you to — this would be a DIY project, not something Nori Robotics or this server has already
> worked out."

### `nori_session` — opening, closing, and checking your connection

This is almost always your second call, right after (or instead of) `nori_info`. The operations:

- **`connect`**: opens a session. Safe to call repeatedly — if one's already open, it's reused.
  Pass nothing for normal use; pass `force_mock=true` if you want to deliberately test against
  the mock even though real credentials are configured.
- **`disconnect`**: closes the session. Also safe to call when nothing's open.
- **`status`** (default): tells you connection state, mock-vs-real, and — if connected —
  telemetry, robot status, daemon status, camera layout.
- **`wait_ready`**: blocks until the robot reports itself fully ready, then hands back detailed
  robot info. Use this before anything time-sensitive, when you need certainty the robot is
  actually up rather than merely connected.

Example:

> **You**: "Connect and tell me the battery level."
>
> **Claude**: *(calls `nori_session(operation="connect")`, then `status`)* "Connected — mock
> session. Note: the mock doesn't report a real battery percentage the way hardware telemetry
> would; that field will populate meaningfully once you're on a real unit."

This is a good moment to notice something important: Claude should tell you honestly when a
mock-session value isn't meaningful, rather than presenting synthetic numbers as if they were
real sensor readings.

### `nori_control` — moving the robot (or the mock)

Everything here requires an open session first. If you try to jog before connecting, you'll get
a clear "no active session" error — that's correct, expected behavior, not a bug.

- **`jog`**: a one-shot, time-bounded movement. Give it a payload describing the motion and a
  duration in seconds.
- **`set_jog`**: a *continuous* jog that keeps going until you explicitly clear it with
  `clear_jog`. Use this only when you actually want ongoing motion, and always follow up with
  `clear_jog` when you're done — don't leave it running.
- **`clear_jog`**: stops a continuous jog started by `set_jog`.
- **`action`**: send specific joint/gripper targets, optionally waiting for the move to finish.
- **`pose`**: Cartesian control — tell it which arm (`left`/`right`), a target `[x, y, z]`
  position in meters, and optionally an orientation quaternion.
- **`estop`**: immediate stop. No arguments, no session-state prerequisites beyond having a
  session at all. If you're ever unsure or uneasy about what the robot is doing, ask for this —
  it costs nothing.
- **`estop_confirmed`**: like `estop`, but waits for an explicit confirmation within a timeout
  you specify.
- **`reset_latch`**: clears an e-stop latch so the robot can move again. Only ask for this once
  you're sure it's actually safe to resume.
- **`reset_arm`**: recovers one specific arm (`left` or `right`) from a fault state.

Example — a cautious motion test:

> **You**: "Jog the left arm gently for half a second, then tell me what happened."
>
> **Claude**: *(calls `nori_control(operation="jog", payload={...}, duration=0.5)`)* "Done —
> the mock reports the jog completed successfully with no faults. Since this is the mock
> session, no physical arm moved; this confirms the command path and payload shape are correct."

Example — safety-first framing:

> **You**: "Actually, stop everything, I'm not comfortable with this."
>
> **Claude**: *(calls `nori_control(operation="estop")` immediately, without asking for
> clarification first)* "E-stopped. The robot (or mock) is now halted. Let me know when — or if
> — you'd like to resume; I'll need to clear the latch first."

That's the correct pattern: e-stop first, discuss afterward. Never expect Claude to negotiate
before honoring a stop request.

### `nori_recording` — capturing demonstrations in LeRobot format

Also requires an open session. This is the tool you want when your goal is training data, not
just moving the robot. The operations map directly onto Nori's own SDK vocabulary rather than a
simplified fleet abstraction, which means there's a real distinction between a *session* (the
outer recording context) and an *episode* (one take within it):

- **`session_start`**: opens a capture session — doesn't record anything by itself yet.
- **`episode_start`** (with a `task` description): begins recording one episode. This is the
  call that actually starts capturing, not `session_start`.
- **`episode_stop`**: ends the current episode's recording.
- **`episode_discard`**: throws away the episode currently being recorded.
- **`session_end`**: closes the whole session, keeping every episode recorded within it.
- **`session_discard`**: closes the session and discards *everything* recorded in it — this one
  is destructive, use it deliberately.
- **`start`** (with `task`): a simpler shortcut that opens a session and starts recording in one
  step, for when you don't need the fine-grained session/episode distinction.
- **`stop`** / **`discard`**: stop or discard whatever's currently active, whichever level that
  is.
- **`discard_last`**: throws away only the most recently *completed* episode, leaving anything
  currently in progress untouched.
- **`status`** (default): recording state, whether a session is open, episode count, free disk
  space.
- **`snapshot`**: grabs one still frame. Important: the mock session has no video track by
  default, so a snapshot against mock will genuinely time out after 20 seconds unless you ask
  for a short `track_timeout` — that's correct behavior demonstrating an honest failure path,
  not a malfunction.
- **`frames`**: returns the camera layout description (not a live video stream).
- **`set_bitrate`** / **`set_paused`**: adjust or pause the live video feed.

Example — recording a demonstration:

> **You**: "Start recording a demonstration of pouring water into a cup."
>
> **Claude**: *(calls `nori_recording(operation="episode_start", task="pour water into cup")`)*
> "Recording started — episode is now active under task 'pour water into cup'. Let me know when
> you're done and I'll stop it."
>
> **You**: "Done, stop it."
>
> **Claude**: *(calls `nori_recording(operation="episode_stop")`, then `status`)* "Episode
> stopped and kept. You now have 1 episode recorded in this session. Want to record another, or
> end the session and keep what you have?"

Example — the snapshot timeout, explained rather than treated as a bug:

> **You**: "Grab a snapshot from the camera."
>
> **Claude**: *(calls `nori_recording(operation="snapshot", track_timeout=2.0)`)* "That timed
> out — expected on the mock session, which doesn't simulate a real video track. This will work
> once you're on real hardware with an actual camera feed."

### `nori_help()` — a fast reset

No arguments. If you (or Claude) lose track of the tool surface mid-conversation, this returns
the tool list and the typical order things happen in: info (optional) → connect → wait_ready
(optional) → control/recording → shutdown or disconnect.

### `nori_shutdown()` — ending cleanly

No arguments. Closes whatever session is open without stopping the MCP server itself — you can
immediately reconnect afterward if you want to start fresh. Prefer this (or `nori_session
(operation="disconnect")`) over just walking away from an open session when you're done.

## More worked examples, covering the rest of the tool surface

The walkthroughs above cover the operations you'll reach for most often. Here are examples for
the rest, so nothing in the tool surface is a surprise the first time you need it.

> **You**: "Before we do anything with the robot, wait until it's fully ready and tell me its
> info."
>
> **Claude**: *(calls `nori_session(operation="connect")`, then `wait_ready`)* "Session ready —
> `wait_ready` blocked until the robot (mock, in this case) reported itself operational, then
> returned its RobotInfo: model, firmware version, and current mode. It's ready for commands."

`wait_ready` matters most right after a fresh `connect`, or after recovering from a fault, when
you want certainty rather than just "connected" — connection and readiness aren't the same
thing, and jumping straight into motion commands before the robot is actually ready can produce
confusing failures that have nothing to do with your command itself.

> **You**: "Set a continuous jog on the base moving forward slowly, I want to watch it for a
> bit, then stop it when I say."
>
> **Claude**: *(calls `nori_control(operation="set_jog", payload={...})`)* "Continuous jog
> started. I'll keep it running until you tell me to stop — just say the word and I'll call
> clear_jog immediately."
>
> **You**: "Okay, stop."
>
> **Claude**: *(calls `nori_control(operation="clear_jog")`)* "Stopped."

Notice the shape of that exchange: `set_jog` is the one operation in this whole tool surface that
keeps doing something after the call returns, so Claude should always confirm it will track that
open-ended state and stop it promptly when asked, rather than treating it like a fire-and-forget
command the way `jog` or `action` are.

> **You**: "Move the right arm to 30cm forward, 10cm right, 20cm up from its current reference
> point, and wait until it's actually there before telling me."
>
> **Claude**: *(calls `nori_control(operation="pose", side="right", position_m=[0.3, 0.1, 0.2],
> wait=true)`)* "Arrived — the pose call returned only after the arm reported reaching that
> Cartesian target."

`pose` is the tool for "put the arm at this specific point in space," as opposed to `action`,
which is the tool for "set these specific joint/gripper values directly." Use `pose` when you're
thinking in terms of where something should end up; use `action` when you already know the exact
joint targets you want.

> **You**: "The left arm faulted during that last move. Can you recover it without resetting
> everything else?"
>
> **Claude**: *(calls `nori_control(operation="reset_arm", arm="left")`)* "Left arm reset — this
> only touches that arm's fault state, the right arm and the rest of the session are untouched."

> **You**: "I e-stopped a minute ago. I've checked and it's safe now, please resume."
>
> **Claude**: *(calls `nori_control(operation="reset_latch")`)* "Latch cleared, the robot can
> accept motion commands again. Note I'm relying on your confirmation that it's actually safe —
> I have no independent way to verify that."

That last line matters: Claude cannot see the room the robot is in. `reset_latch` should always
be treated as something done on your explicit say-so, never inferred or assumed.

> **You**: "I want the fine-grained version — open a recording session but don't start capturing
> yet, I need to get in position first."
>
> **Claude**: *(calls `nori_recording(operation="session_start")`)* "Session opened, not yet
> recording. Say the word and I'll call episode_start with whatever task label you want."
>
> **You**: "Okay, go — task is 'stack three blocks'."
>
> **Claude**: *(calls `nori_recording(operation="episode_start", task="stack three blocks")`)*
> "Recording now."

That two-step `session_start` → `episode_start` pattern is the one to reach for when you need a
setup pause between opening the session and actually capturing — the simpler `start` shortcut
collapses both into one call for when you don't need that pause.

> **You**: "Actually scrap that whole session, none of it was good."
>
> **Claude**: *(calls `nori_recording(operation="session_discard")`)* "Session and every episode
> recorded within it have been discarded — this is not recoverable, so I want to flag that
> before confirming: is that definitely what you wanted, including episodes from earlier in this
> session, not just the current one?"

Because `session_discard` is destructive and irreversible, expect Claude to double-check intent
before or immediately after calling it, rather than executing it as casually as, say, `episode_
discard`, which only affects the single in-progress take.

> **You**: "Turn the video bitrate down, I'm on a slow connection, and pause it entirely for a
> minute while I step away."
>
> **Claude**: *(calls `nori_recording(operation="set_bitrate", kbps=500)`, then `nori_recording
> (operation="set_paused", paused=true)`)* "Bitrate lowered to 500kbps and the live stream is
> paused. Say when you're back and I'll unpause."

> **You**: "What's the deal with this robot's software lineage — is it built from scratch?"
>
> **Claude**: *(calls `nori_info(operation="predecessor")`)* "No — the A3 descends from
> XLeRobot, an open-source bimanual platform. [summarizes what specifically carried forward]."

> **You**: "Where's the actual SDK source, and what license is it under?"
>
> **Claude**: *(calls `nori_info(operation="sdk_links")`)* "It's `nori-sdk-py` on GitHub,
> published to PyPI as `nori-sdk`, Apache-2.0 licensed. It speaks a WebRTC data-channel protocol
> with Supabase Realtime for signaling, and records into the LeRobot dataset format."

> **You**: "If I wanted to train a model on the demonstrations I record here, what would I use?"
>
> **Claude**: *(calls `nori_info(operation="fleet_peers")`)* "Your recordings are already in
> LeRobot format, so `vla-mcp` in this same fleet is built to consume them directly for policy
> training. If you also want VR-driven teleoperation instead of typed commands for data
> collection, `teleoperator-mcp` is the one for that."

## A full end-to-end conversation, start to finish

Putting several tools together in the order you'd realistically use them:

> **You**: "I want to record three demonstrations of picking up a cup today. Walk me through it."
>
> **Claude**: "Sure. First I'll connect a session and confirm the robot's ready."
> *(calls `nori_session(operation="connect")`, then `wait_ready`)*
> "Connected and ready — this is running on the mock session, by the way, since no real-hardware
> credentials are configured. I'll open a recording session now."
> *(calls `nori_recording(operation="session_start")`)*
> "Recording session open. Tell me when you're ready for episode one."
>
> **You**: "Go."
>
> **Claude**: *(calls `nori_recording(operation="episode_start", task="pick up cup")`)*
> "Recording episode 1."
>
> **You**: "Done with that one."
>
> **Claude**: *(calls `nori_recording(operation="episode_stop")`)* "Episode 1 stopped and kept.
> Ready for episode 2 whenever you are."
>
> *(...the same episode_start / episode_stop pair repeats for episodes 2 and 3...)*
>
> **You**: "That's all three, let's wrap up."
>
> **Claude**: *(calls `nori_recording(operation="status")`)* "You have 3 episodes kept in this
> session."
> *(calls `nori_recording(operation="session_end")`)*
> "Session closed, all 3 episodes preserved."
> *(calls `nori_shutdown()`)*
> "And the robot session is shut down cleanly. Whenever you want to train on these, `vla-mcp`
> can pick up straight from the LeRobot-format dataset that just got written."

This is the shape of a well-run session: explicit about mock-vs-real up front, clear narration
of what's happening at each step, and a clean, deliberate close rather than just trailing off.

## Configuration: moving from mock to real hardware

When your A3 arrives, moving from mock to real involves setting environment variables, not
changing how you talk to Claude. The three that gate real-hardware mode, all required together:
`NORI_MCP_SUPABASE_URL` (your Supabase project URL), `NORI_MCP_SUPABASE_ANON_KEY` (the
anonymous key), and `NORI_MCP_ROBOT_ROOM` (your robot's signaling-room identifier, something
like `NORI-A3-0001`). You'll also want `NORI_MCP_USER_EMAIL` and `NORI_MCP_USER_PASSWORD` set to
your Nori account credentials, used for token refresh. If even one of the three required
variables is missing, every session silently falls back to mock — there's no partial-credit
state, which is a deliberate safety property, not an oversight.

If you're running this server standalone (outside Claude Desktop) rather than through this
MCPB bundle, two more variables matter: `NORI_MCP_HOST` (default `127.0.0.1`) and `NORI_MCP_PORT`
(default `11970`) control where its HTTP API and dashboard-facing endpoints bind. Inside Claude
Desktop, none of that applies — the server runs over stdio and you never touch ports directly.

## Troubleshooting

**"Every session reports mock: true, even though I set up Supabase."** Double-check all three
required variables are set and correctly spelled — `NORI_MCP_SUPABASE_URL`, `NORI_MCP_SUPABASE_
ANON_KEY`, `NORI_MCP_ROBOT_ROOM`. The fallback triggers if even one is missing.

**"Claude says 'no active session' when I ask it to move the arm."** You (or Claude) skipped
`nori_session(operation="connect")`. Ask Claude to connect first — every control and recording
call needs an open session as a prerequisite, and this failure mode is working as intended.

**"A snapshot or camera call times out."** Expected against the mock session, which has no
simulated video track. This resolves itself once you're connected to real hardware with an
actual camera.

**"estop_confirmed doesn't come back."** On the mock, this can be deliberate — the mock is built
to be configurable into `accepted=False` / `online=False` states specifically so failure paths
can be exercised safely. On real hardware, a timeout here means the confirmation never reached
the robot's control channel; check `nori_session(operation="status")` for the WebRTC connection
state before assuming anything else is wrong.

**"I'm not sure if something actually moved."** Ask directly: "was that mock or real?" Claude
has access to the mock/real flag from every session status call and should answer precisely
rather than hedge.

## Frequently useful requests, phrased naturally

You don't need to know tool names or parameter shapes to use this server — plain requests work
fine, and Claude will map them onto the right calls:

- "What's the Nori A3 and how much does it cost?"
- "What did the Hacker News crowd think when this launched?"
- "Open a session and tell me the current status."
- "Is this the real robot or the mock right now?"
- "Move the right arm to [some position], carefully, and confirm before doing anything else."
- "Stop everything right now." (should trigger `estop` immediately, no back-and-forth first)
- "Clear the e-stop, I've confirmed it's safe."
- "Start recording me demonstrating [some task]."
- "Stop the recording and tell me how many episodes I have so far."
- "Discard that last episode, I made a mistake."
- "Grab a camera snapshot." (expect a timeout explanation if you're on mock)
- "Close the session, we're done for now."
- "What other robots or MCP servers does this connect to?"
- "Walk me through what I'd need to set up to use my real A3 once it ships."

## FAQ

**Do I need to own the robot to use this server?** No. Every tool works fully against the mock
session, and most people will use this server extensively before a physical unit ever arrives.

**Will this ever accidentally control someone else's robot?** No — sessions are scoped to the
`NORI_MCP_ROBOT_ROOM` you configure, tied to your own Nori account credentials. Without your
specific real-hardware configuration, every session is local and mock.

**Can I run this alongside Nori Robotics' own `lab.norirobotics.com` dashboard?** Yes, they're
independent — this server doesn't replace or conflict with Nori's own web app; it's a separate,
conversational way to reach the same underlying SDK.

**What happens to episodes I record if I never configure real hardware?** They're still real,
valid LeRobot-format recordings — just recorded from the mock's synthetic motion rather than a
physical demonstration. Useful for testing a training pipeline end-to-end before you have
real data to feed it, but don't mistake them for genuine demonstrations when it matters.

**Is it safe to experiment freely with `nori_control` operations?** Yes, on the mock session,
which is the default — nothing physical is at risk. Once you're on real hardware, treat every
motion command with the same care you'd use operating the physical robot directly, and remember
`estop` is always one call away, at zero cost.

## A note on honesty and expectations

This server, and Claude when using it, will not pretend the mock session is a real robot, will
not invent sensor readings or specs beyond what the tools actually return, and will not report a
safety operation as successful without a real response confirming it. If something the tools
don't cover comes up — a feature Nori Robotics hasn't documented, a spec that isn't in `nori_
info`'s data — the correct answer is "I don't know," not a plausible-sounding guess. That
discipline is what makes it safe to explore this server freely before you ever own a physical
unit, and just as safe to keep using once you do.
