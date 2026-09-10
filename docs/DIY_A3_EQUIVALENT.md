# Building an A3-Equivalent (or Better): A Full DIY Project

This is not "buy XLeRobot instead" — XLeRobot is a real, excellent $660 open project, but it's a
lighter-duty predecessor (5-DOF arms, ~40cm reach, 600–1000g/arm, no telescoping lift), not an A3
equivalent. This doc targets **matching or exceeding every A3 spec**: 55cm reach, 1.5kg payload
per arm, a 69–145cm telescoping working range, four cameras, 2D LiDAR, a mic array, and a fully
open software stack — built from commodity and open-hardware parts, with the actual engineering
math shown, not hand-waved.

Two tiers are costed throughout: **Match** (same actuator class as Nori A3 — Feetech-grade,
cheapest path to the same numbers) and **Exceed** (QDD actuators from
[`ACTUATOR_ALTERNATIVES.md`](ACTUATOR_ALTERNATIVES.md) — meaningfully more expensive, genuinely
better force feedback and headroom). Both are honest about where they land relative to A3's
$1,688 — spoiler: Match can beat it, Exceed generally can't, and that tension is the actual point
of showing both.

## What we actually have, and the one hard limit on "duplicate"

This repo already carries Nori Robotics' own official description package
(`models/nori_description/` — CC BY-NC-SA 4.0, Copyright 2026 Nori Robotics Inc.): real,
hardware-verified URDF kinematics (joint axes, limits, link transforms), visual STL meshes for
every arm segment, and the ROS2 control interface definitions. That's a genuinely better starting
point than reverse-engineering from photos or video — the joint geometry below is measured, not
estimated.

**The package's own `NOTICE` says these aren't manufacturing-ready** — worth checking that claim
against the actual files rather than taking it purely on faith, since "not manufacturing data" is
doing a lot of work and could mean anything from "genuinely fake" to "needs cleanup." Direct
inspection (`trimesh`) of a few parts:

| Mesh | Vertices | Faces | Watertight | Bounding box |
|---|---|---|---|---|
| `shoulder_pitch.stl` | 2,624 | 4,369 | **No** | 68 × 64 × 79 mm |
| `gripper_r.stl` | 4,718 | 10,285 | **No** | 34 × 104 × 55 mm |
| `elbow_pitch.stl` | 2,770 | 5,910 | **No** | 45 × 145 × 84 mm |
| `base_shell.stl` | 9,992 | 7,764 | **No** | 393 × 270 × 207 mm |

**The shapes are real** — thousands of faces each, physically plausible robot-component
dimensions, not placeholder boxes. (The LiDAR mesh and the torso/neck/head shapes *are* explicitly
flagged as placeholders/stand-ins in `NOTICE` — a narrower, separate claim from "the arm meshes
aren't real.") **The concrete problem is `watertight=False` on every part checked** — that's the
measurable meaning of "internal geometry removed, surfaces decimated": these are open shells with
gaps in their boundary, not closed solids. Slicing a non-watertight mesh directly either fails
outright or triggers a slicer's own gap-filling guess, which won't match the real part's actual
wall thickness or fastener bosses. That's a real, checkable fact, not vendor over-caution.

**This is a mesh-repair-and-reconstruct problem — and this repo's own fleet already has the right
tools for exactly that job**, not a "design everything from a rough visual reference" problem:

- **`blender-mcp`**: fill the holes, recalculate normals, and run a solidify/shell operation at a
  chosen real wall thickness to turn each open decimated shell into an actual closed, printable
  solid. This is routine practice in the replacement-parts/prop-making 3D-printing community for
  exactly this class of source file (a public reference mesh, not vendor CAD) — not exotic.
- **`qcad-mcp`**: verify the repaired geometry's critical dimensions (joint pivot locations, bolt
  spacing, mounting patterns) against the URDF's own joint transforms — which `NOTICE` states
  plainly ARE measured and hardware-verified, independent of the surface-mesh caveat above.
  The skeleton is real and accurate; it's specifically the surface *skin* that needs
  reconstruction, and that distinction is what makes this tractable rather than a guess.

So: real external shape, real accurate joint geometry underneath, a genuinely open (non-watertight)
surface that needs repair before it's a print-ready solid — reconstruct it with the tools already
in this fleet rather than either printing it blind or discarding it as unusable.

**License note**: CC BY-NC-SA 4.0 covers this package specifically — personal/research use,
share-alike, **no commercial use** without contacting Nori Robotics directly. A hobbyist DIY build
for yourself is squarely inside the license; selling clones is not.

**Real numbers worth designing to**, pulled directly from the expanded URDF and `NOTICE` rather
than the rounded marketing spec sheet:
- Lift: **3 stages**, commanded travel **700mm** (`lift_extension_joint`, limit 0.0–0.700m),
  physical stroke **720mm** (20mm mechanical-stop reserve, not commanded). Middle stage moves at
  exactly **0.5x** the top stage's rate (`mimic` joint, multiplier 0.5) — a real, verifiable
  synchronization ratio to replicate, not an assumption.
- Real total mass is **20.5kg** — the modeled links sum to 18.3kg; scale by **1.121** to account
  for wiring loom, USB hubs, and fasteners not modeled as their own link.
- Gripper is a **geared two-finger claw** — one servo-driven finger, one idler finger on a mimic
  joint (`arm.xacro`: "the gripper is a geared two-finger claw: one servo-driven finger plus an
  idler finger on a mimic joint"). **Not three-finger** — worth correcting up front, since a
  3-finger design (see below) would be a deliberate *upgrade* over A3's own choice, not a
  duplication of it.

## Design targets

| Spec | Nori A3 | This build's target |
|---|---|---|
| Arms | 2x 7+1 DOF, 55cm reach, 1.5kg payload | Match or exceed |
| Lift | 3-stage telescoping, 700mm commanded / 720mm physical stroke (measured — see below) | Match |
| Base | Differential drive + casters, 45x45cm | Match, holonomic as upgrade option |
| Compute | Raspberry Pi 5, 4GB (I/O + control loop only) | Match or exceed (Pi 5 8GB / Jetson Orin Nano) |
| Cameras | 4x 720p (grippers x2, head, neck) | Match |
| LiDAR | 2D, 12m range, 8–12Hz | Match — RPLidar A1 is a documented near-exact fit |
| Audio | Dual-mic array, onboard speaker | Match |
| Software | Apache-2.0 SDK, cloud-mediated (WebRTC + Supabase) | **Exceed** — fully local, no cloud dependency |

## The load-bearing engineering fact: why "cheap actuators" isn't just cost-cutting

Before picking parts, do the torque math A3's own spec sheet implies. Holding 1.5kg **statically**
at 55cm reach needs:

```
τ = F × r = (1.5 kg × 9.81 m/s²) × 0.55 m ≈ 8.1 N·m
```

That's *before* the arm's own weight, any dynamic motion, or safety margin. Nori A3's own shoulder
actuator — the STS3095 at 95 kg·cm (≈9.3 N·m) — is sitting almost exactly at that number. This
isn't a coincidence or a marketing rounding: **1.5kg @ 55cm is genuinely the ceiling a 9.3 N·m
actuator can support**, and it's why `docs/REVIEW.md` flags payload as a real gap rather than
false modesty. Any DIY build targeting the same numbers inherits the same constraint — you cannot
hit A3's payload/reach spec with SO-101's stock STS3215 (30 kg·cm ≈ 2.9 N·m) at the shoulder. The
base SO-101/SO-ARM100 mechanical design (open, proven, native LeRobot support) is still the right
starting point — but the shoulder and elbow joints need an actuator upgrade to get there.

## Arms: SO-101 mechanical design, upgraded actuators at the load-bearing joints

Base kit: [SO-ARM101](https://www.seeedstudio.com/SO-101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html) —
6-DOF, 3D-printed structure, native Hugging Face LeRobot support, ~$199/arm complete,
~$115–150/arm motor-only if 3D-printing your own structure
([TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100/blob/main/README.md)).

**Match tier** — replace the shoulder (and ideally elbow) joint servos with Feetech's own STS3095
(95 kg·cm ≈ 9.3 N·m, the exact part Nori A3 uses at this joint). No confirmed unit price found in
this pass — extrapolating from the STS3215→STS3250 price curve ($16→$55 for 30→50 kg·cm) puts
STS3095 plausibly in the **$70–120 range**; confirm directly before budgeting. Keep STS3215/3250
everywhere else (wrist, gripper) — those joints don't carry the static payload load.

**Exceed tier** — replace the same joints with a QDD actuator from `ACTUATOR_ALTERNATIVES.md`'s
comparison table: a Damiao DM-J4340 (27 N·m, ~3x A3's own shoulder torque) or a RobStride 01/02
(17 N·m, ~$260-class) genuinely exceeds A3's payload ceiling **and** gets native FOC current-
sensing force feedback instead of Nori's software-current-polling workaround — a real capability
upgrade, not just a bigger number. Requires a different mounting bracket (these are round-body
QDD modules, not Feetech's rectangular servo horn pattern) and 24–48V wiring vs. the rest of the
arm's 12V bus — a real integration task, not a drop-in swap.

## The telescoping lift: what A3 actually uses, and two real alternatives

This is the actual missing piece — XLeRobot/Lekiwi mounts its arms at a **fixed** height on an
IKEA cart. Nori A3's whole capability multiplier (per `HOME_ROBOT_PARADIGM.md`) is that the column
moves, through the real, measured **700mm commanded / 720mm physical**, 3-stage travel documented
above.

**A3's own paper says directly what the mechanism is** — not a guess, a quote
([arXiv:2605.16537](https://arxiv.org/html/2605.16537)):

> "A three-stage steel telescoping column, of the type used for height-adjustable desks and
> comparable to YOR's, replaces the fixed-stroke ball screw of the prior version."

Two real things fall out of that: A3's lift **is** a commodity standing-desk-category column, not
a bespoke robotics part dressed up to look like one — the DIY option below isn't an approximation
of A3's mechanism, it's the same category the shipping robot actually uses. And Nori's own earlier
prototype used a **ball screw** first and moved away from it — the precision alternative below was
tried and superseded, not overlooked. ("YOR" is quoted as a comparison point in the paper but
doesn't match any lift-column brand found in this research pass — LINAK, TiMOTION, Uplift,
Progressive Desk, and Firgelli were all checked directly; worth resolving before treating it as a
sourcing lead rather than repeating it as fact.)

**1. Repurposed electric standing-desk column — this is what A3 itself uses, not just a
lookalike.**
- Individual linear actuators (12–18V, 16–18" stroke): **~$80/unit on eBay**, rated 220–600 lbs
  lift capacity each ([Firgelli's DIY column guide](https://www.firgelliauto.com/blogs/standing-desks/diy-standing-desk-choosing-the-right-telescopic-column-lift))
  — wildly over-specced for an arm assembly's weight, which is the point: massive margin at low
  cost, furniture-industry economics instead of robotics-industry economics.
- A full DIY dual-actuator build (structural tube + 2 actuators + controller) runs **$175–400** in
  parts, 5–6 hours of build time ([DIY standing desk build log](https://www.davidgunter.com/2020/07/23/diy-electric-standing-desk/)).
- Most off-the-shelf desk columns are 2-stage, not A3's 3-stage, and don't natively give a clean
  0.5x mimic relationship out of the box — matching A3's exact 3-stage/0.5x ratio still takes
  picking (or gearing) the right column, not just buying "a" standing-desk actuator.

**2. Ballscrew/lead-screw linear rail + NEMA17 stepper — the road not taken by A3, for good
reason to know about.**
A 200mm SFU1605 ballscrew rail with a NEMA17 stepper runs **~$78/unit**
([eBay listing](https://www.ebay.de/itm/187709575827)) — the exact mechanism category 3D
printers and CNC machines already use, so tooling, drivers, and community knowledge are abundant.
It's genuinely more precise and quieter than a desk-column actuator — which makes it worth
understanding *why A3's own team moved away from it*: a fixed-stroke ball screw ties stowed height
to a single screw's length, while nested telescoping stages (option 1) decouple stowed height from
extended reach — exactly the design rationale the paper gives for the switch. A DIY build
optimizing purely for precision could still choose this path, but should go in knowing it's
solving a different problem than the one A3's own engineers decided mattered more.

**Recommendation**: build the standing-desk-column version (option 1) — it's cheaper, it's what
the actual robot uses, and Nori's own move away from ball-screw is a real, sourced reason to
prefer it over the more precise-sounding alternative rather than assuming precision wins by
default.

## Grippers: A3's own 2-finger claw, vs. a real 3-finger upgrade

**Match tier — reproduce A3's actual design.** Per the URDF comment above, A3's gripper is a
simple geared two-finger claw: one servo-driven finger, one idler finger slaved to it via a mimic
joint. Mechanically simple, cheap, matches the "push cost into software, not hardware" philosophy
in `HOME_ROBOT_PARADIGM.md` — but it's a fundamentally two-point grip, less secure on irregular
or round objects than a three-point one.

**Exceed tier — a real open-source 3-finger design.** This is a deliberate upgrade over A3's own
choice, not a duplication of it, and there's real prior art to build from rather than designing
from scratch:
- **[Yale OpenHand Model O](https://www.wevolver.com/specs/3d.printed.robotic.gripper.1)** — a
  3-finger, 4-DOF, mostly-3D-printed underactuated hand, fully open source, one of the
  longest-standing reference designs in this space.
- **[RAMEL-ESPOL Three-Fingered Robotic Gripper](https://github.com/RAMEL-ESPOL/Three-Fingered-Robotic-Gripper)**
  (2024–2025) — PLA for rigid structure, TPU for flexible membranes, actively maintained GitHub
  repo with real STLs — a more current starting point than Model O if you want a maintained
  project rather than a decade-old reference design.
- The original **Alaris underactuated 3-finger gripper** (2014) — four-bar-linkage + worm-gear
  actuation from a single off-the-shelf servo, one of the first fully open low-cost designs in
  this category ([IEEE paper](https://ieeexplore.ieee.org/document/6935605/)).

An underactuated 3-finger design (one motor driving all three fingers through a linkage, rather
than three independently actuated fingers) keeps the actuator count and cost close to A3's own
2-finger claw while genuinely improving grip security on round/irregular objects — the sensible
middle ground between "duplicate A3 exactly" and "over-engineer a fully dexterous hand."

## Base: differential drive (match) or holonomic (exceed)

**Match tier**: differential drive + passive casters, matching A3's 45x45cm footprint exactly —
two drive wheels (any commodity 12V geared DC motor + wheel, ~$15–30/side) plus 2 casters. Simpler
kinematics, cheaper, more robust than omni-wheels, and it's what A3 itself actually ships with —
there's no reason to over-engineer past the reference design here.

**Exceed tier**: a Lekiwi-style holonomic base (3x omni-wheels, as used in XLeRobot) trades some
simplicity for the ability to strafe sideways in a cluttered apartment aisle without a three-point
turn — a genuine maneuverability upgrade A3 doesn't have. XLeRobot's own BOM
([material list](https://xlerobot.readthedocs.io/en/latest/hardware/getting_started/material.html))
is the reference for this option.

## Compute, sensors, audio

- **Compute**: Raspberry Pi 5 (4GB matches A3 exactly; 8GB for headroom) for the safety-critical
  I/O/control loop, same split-compute philosophy as A3 (`HOME_ROBOT_PARADIGM.md`) — the "strong
  AI" policy runs off-board regardless of what's onboard. A Jetson Orin Nano (seen bundled in one
  XLeRobot expansion-kit listing) is a real **exceed** option if you want some onboard inference
  headroom A3 deliberately doesn't have — but that's a scope decision, not a requirement to match
  A3's own architecture.
- **Cameras**: 4x cheap USB webcams (grippers x2, head, neck — same placement logic as A3) at
  commodity pricing, easily matching 720p per camera.
- **LiDAR**: [RPLidar A1](https://www.slamtec.com/en/lidar/a1) — 360°, **12m range**, up to 10Hz
  scan rate, <0.5mm resolution within 1.5m — this is a near-exact documented match to A3's own
  cited LiDAR spec (12m range, 8–12Hz), at **$180–220** retail
  ([Adafruit](https://www.adafruit.com/product/4010), [RobotShop](https://www.robotshop.com/products/rplidar-a1m8-360-degree-laser-scanner-development-kit)),
  real operational cost closer to $300 once a controller/adapter is included. This is the single
  most expensive sensor line item in the whole build.
- **Audio**: commodity USB dual-mic arrays exist at low cost; match A3's full-duplex capability by
  confirming the specific module supports simultaneous record+playback, not just record.

## Software: fully local is the "even better" that matters most

Nori A3's control path is cloud-mediated — WebRTC data channel, Supabase Realtime signaling,
requiring an internet connection and a third party's infrastructure to operate a robot inside your
own home (the exact point the HN launch thread's privacy/telemetry criticism targeted, per
`REVIEW.md`). A DIY build using the **Hugging Face LeRobot stack directly** — the same software
lineage Nori's own SDK is compatible with at the dataset-format level — runs entirely locally: USB
or direct-wire connection to the arms, no cloud signaling layer required. This is the one place a
DIY build is unambiguously *better* than buying A3, not just cheaper or more customizable: no
account, no third-party infrastructure dependency, no telemetry question to even ask.

The real DIY engineering debt this creates: Nori's actuator-protection layer (thermal/stall
protection derived from servo current, per `HOME_ROBOT_PARADIGM.md`) is **not** part of stock
LeRobot — it's Nori-specific safety software built on top. A DIY build matching A3's actual
day-to-day robustness needs an equivalent protection layer written from scratch (poll
`Present_Current`, set thermal/stall thresholds, cut power on latch) — straightforward with
Feetech's own register map, genuinely new work, not a checkbox.

## Cost rollup

| Component | Match tier | Exceed tier |
|---|---|---|
| 2x arms (SO-101 base + shoulder/elbow upgrade) | ~$400 kits + ~4×$70–120 upgraded joints ≈ **$680–880** | ~$400 kits + ~4×$260 QDD joints ≈ **$1,440** |
| Telescoping lift (DIY standing-desk actuator pair) | **$175–400** | same |
| Base (differential drive, match) | **~$60–100** | Lekiwi-style holonomic ≈ **$150–250** |
| Compute (Pi 5) | **~$80** | Jetson Orin Nano ≈ **$250+** |
| 4x cameras | **~$60–120** | same |
| RPLidar A1 + adapter | **~$220–300** | same |
| Mic array + speaker | **~$40–80** | same |
| Structure, fasteners, wiring, PSU, misc | **~$150–250** | same |
| **Total (rough)** | **≈ $1,400–2,100** | **≈ $2,700–3,600** |

**The honest read**: Match tier lands in or just above A3's own $1,688 — a real DIY build can be
roughly cost-competitive with the factory-assembled unit while running fully local, at the cost of
real assembly time, no warranty, and no professional calibration pass. Exceed tier is meaningfully
more expensive — genuinely better actuators and force feedback aren't a free upgrade, they're a
real trade against the price-band thesis in `HOME_ROBOT_PARADIGM.md`. Both are legitimate answers
depending on whether the goal is "match A3 as cheaply as possible" or "build the thing A3 would be
if cost weren't the primary constraint."

## Sourcing: what to source from Shenzhen vs. what to make locally

Following `ACTUATOR_ALTERNATIVES.md`'s sourcing section directly: **actuators and electronics are
the components worth ordering from Shenzhen-adjacent suppliers** (every vendor in that doc's
comparison table — CubeMars, MyActuator, Damiao, RobStride — ships from China; at joint-count
quantities, hobbyist-tier resellers like RobotShop/Seeed Studio/AliExpress are simpler than a
direct 1688.com/Alibaba B2B import, and the price difference at 2–8 units is small). **Structural parts are the opposite** — the official mesh package's arm-segment shells are real
but non-watertight (see above), so the path is repair-then-print, not source-then-print: run the
`blender-mcp`/`qcad-mcp` reconstruction pass described above to get real, solid, correctly-
walled parts, then 3D-print locally or through a local/regional service where you can inspect
tolerances directly before final assembly on a powered-arm-and-lift machine. Don't outsource the
one part where "will it actually fit and hold together safely" needs your own eyes on the result.

## What a DIY build gives up, regardless of tier

No professional integration pass, no warranty, no plug-and-play calibration, no vendor support
line, and the actuator-protection safety layer is homework, not a checkbox. This is a project for
someone who wants to own the whole stack, not a faster or cheaper way to get a turnkey robot.

## References

- [`models/nori_description/`](../models/nori_description/) — this repo's own copy of Nori's official URDF/mesh package (CC BY-NC-SA 4.0); see its `NOTICE` and `LICENSE` files directly before relying on any dimension from it
- `blender-mcp`, `qcad-mcp` — fleet repos for the mesh-repair (watertight/solidify) and parametric-verification pass described above
- [XLeRobot](https://github.com/Vector-Wangel/XLeRobot) — closest existing open project, useful for base/holonomic-drive reference, not a spec match on its own
- [SO-ARM100/101](https://github.com/TheRobotStudio/SO-ARM100/blob/main/README.md) · [kit @ Seeed Studio](https://www.seeedstudio.com/SO-101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html)
- [`ACTUATOR_ALTERNATIVES.md`](ACTUATOR_ALTERNATIVES.md) — full QDD vendor comparison and PRC-sourcing guidance for the Exceed-tier joints
- Standing-desk telescoping columns: [Firgelli DIY column guide](https://www.firgelliauto.com/blogs/standing-desks/diy-standing-desk-choosing-the-right-telescopic-column-lift) · [DIY build log](https://www.davidgunter.com/2020/07/23/diy-electric-standing-desk/)
- Ballscrew linear rail: [SFU1605 + NEMA17 @ eBay](https://www.ebay.de/itm/187709575827)
- 3-finger grippers: [Yale OpenHand Model O](https://www.wevolver.com/specs/3d.printed.robotic.gripper.1) · [RAMEL-ESPOL GitHub](https://github.com/RAMEL-ESPOL/Three-Fingered-Robotic-Gripper) · [Alaris underactuated gripper (IEEE)](https://ieeexplore.ieee.org/document/6935605/)
- [RPLidar A1 @ Slamtec](https://www.slamtec.com/en/lidar/a1) · [@ Adafruit](https://www.adafruit.com/product/4010)
- [`HOME_ROBOT_PARADIGM.md`](HOME_ROBOT_PARADIGM.md) — the wheels/lift/split-compute philosophy this build follows
- [`REVIEW.md`](REVIEW.md) — the payload/actuator/cloud-dependency gaps this build directly addresses
