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

## Protocol, in one paragraph

`nori-sdk`'s `RemoteTeleop` opens a **WebRTC data channel** to the robot, with **Supabase
Realtime** handling signaling/auth. There is no serial, USB, or local ROS bridge — every real
session is cloud-mediated. For development without hardware, the SDK ships its own
`mock_session()` / `MockRobot`, which this repo uses as the default backend until real Supabase
credentials are configured (see `docs/ONBOARDING.md`).
