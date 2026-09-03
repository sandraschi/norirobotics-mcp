# Wrapped SDK — Nori Robotics A3 / nori-sdk

**Nori A3** is a $1,688, 19-DOF wheeled bimanual home robot from **Nori Robotics** (San
Francisco, Y Combinator S26). It is not to be confused with the many other "home robot"
projects launched in the same window (Noetix Bumi, Unitree humanoids, AgiBot A3 — note the
name collision with AgiBot's unrelated "Expedition A3" / "AGIBOT A3" product) — this repo wraps
specifically **Nori Robotics'** A3, at `norirobotics.com`.

## Official links

- Site: https://www.norirobotics.com/
- Nori Lab (training/teleop webapp): https://lab.norirobotics.com/
- SDK: https://github.com/Nori-Robotics/nori-sdk-py (Apache-2.0)
- PyPI: `nori-sdk` (verified present, v1.1.0 as of this research pass)
- Launch HN: https://news.ycombinator.com/item?id=49525153
- Technical paper: https://arxiv.org/html/2605.16537 ("Nori A3: A Bimanual Mobile Manipulator
  at the Appliance Price Point")

## Community

- Primary community signal found in this research pass is the Hacker News launch thread (97
  points, 36 comments) — see `nori_info(operation="community")` for a structured summary. No
  dedicated Discord/forum was found; check the site footer / GitHub org for updates, as this may
  change post-launch.
- The predecessor lineage (XLeRobot, SO-100/SO-101, Hugging Face LeRobot) has a large, active
  community: 4.8k+ GitHub stars, 6,000+ builders (research-pass snapshot). Nori A3 is a
  from-scratch commercial evolution of that lineage, not a repackaged XLeRobot — see
  `nori_info(operation="predecessor")`.

## Disambiguation

- **Not** the same as Noetix's "Bumi" humanoid (see `bumi-mcp` in this fleet) — different
  company, different form factor (Bumi is bipedal-adjacent; A3 is wheeled).
- **Not** the same as AgiBot's "Expedition A3" / "AGIBOT A3" — coincidental name overlap, unrelated
  company and hardware.
- The SDK repo is named `nori-sdk-py`; the installable PyPI package is `nori-sdk` (no `-py`
  suffix) — easy to typo when writing install docs.

## Founder

**Antonio Sitong Li** is the founder and CTO of Nori Robotics. He studied Computer Science and
Architecture at Columbia University, where he held research fellowships with the **Laidlaw
Scholars Program**, the **Data Science Institute**, and the **Graphics & UI Lab** — his
academic work centered on teaching robots new tasks through VR demonstrations, the same
teleoperated-demonstration model `nori_recording`'s LeRobot-format episode capture is built
around. He holds a national patent for a computer-vision system and previously co-founded
**Truely**, a venture that reached 2,000+ users and 1.5M+ impressions, before starting Nori.

Nori Robotics' stated mission, per its Y Combinator listing, is to "solve the robotics data
bottleneck" — deploying affordable robots widely enough to gather the training data a
generalist robotic policy actually needs, rather than relying on the small, expensive robot
fleets most manipulation research is currently limited to. The $1,688 price point isn't
positioned as a novelty; it's the mechanism for that data-collection thesis to work at all.

Sources: [Y Combinator company page](https://www.ycombinator.com/companies/noril1),
[Launch HN thread](https://news.ycombinator.com/item?id=49525153).

## The Founding Paper

The technical paper behind this robot has a genuinely interesting history, visible directly in
its own arXiv version log — it isn't one static document, it tracks the project's actual
evolution from a course assignment into a funded company:

- **v1** (submitted 2026-05-15): *"Nori Bot: A Sub-$1,000 Floor-to-Counter Mobile
  Manipulator"* — authored by **Antonio Li, Sungjoon Park, and Wen Ni Chew**, a Columbia
  University *Deep Learning Robot Manipulation* course project. Describes a 17-DoF dual-arm
  mobile manipulator at **$947 in parts** (~3% the cost of comparable commercial platforms),
  with a 600mm vertical lift for floor-to-counter reach, proactive autonomous control via a
  Raspberry Pi 4 running the OpenClaw agent runtime, and the same sensorless
  grip-force-via-motor-current technique this robot still uses today.
- **v2** (released 2026-08-22, ~6x the file size of v1): retitled *"Nori A3: A Bimanual
  Mobile Manipulator at the Appliance Price Point"*, now authored solely by **Antonio Li**.
  Describes the shipping 19-DoF, $1,688, Raspberry Pi 5 commercial product this repo wraps —
  roughly one-fifth the parts cost of comparable research platforms, achieved by favoring
  software solutions (a two-tier thermal/stall interlock protecting commodity servos, the
  same sensorless force-sensing carried forward from v1) over expensive actuator hardware.

Read together, the two versions of the same arXiv submission are the clearest available
record of how this specific robot went from a class project to a company: same core
technical bets (telescoping lift, commodity servos protected in software, sensorless force
sensing), refined DoF count and mechanism, and a manufacturing/cost story tightened enough to
actually ship. See [arxiv.org/html/2605.16537](https://arxiv.org/html/2605.16537) for the
current (v2) version, or `nori_info(operation="specs")` for the numbers this server itself
tracks day to day.

## Protocol, in one paragraph

`nori-sdk`'s `RemoteTeleop` opens a **WebRTC data channel** to the robot, with **Supabase
Realtime** handling signaling/auth. There is no serial, USB, or local ROS bridge — every real
session is cloud-mediated. For development without hardware, the SDK ships its own
`mock_session()` / `MockRobot`, which this repo uses as the default backend until real Supabase
credentials are configured (see `docs/ONBOARDING.md`).
