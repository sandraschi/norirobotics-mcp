# DIY Auto-Docking Base Station: Closing A3's Charging Gap

`docs/REVIEW.md` flags this plainly: no charging/docking solution appears anywhere in Nori A3's
sourced material. This doc works the problem from the most proven reference design in consumer
robotics (Roomba's dock, which has had two decades of real-world iteration) through to what a
wheeled differential-drive base like A3's would actually need, with real component specs — pogo
pins, IR homing, mechanical alignment — not a hand-wave.

## How Roomba actually does it — the proven reference design

Worth being precise here because it's easy to mis-describe: **Roomba does not use pogo pins.**
Its charging contact is a pair of flat, exposed metal strips near the front-bottom of the chassis
that make a **wiping contact** against matching plates on the dock's ramp when the robot drives
up onto it — a much more alignment-tolerant contact than a pin array, at the cost of being a
larger, more exposed contact surface.

**Homing**: the dock emits **two distinguishable IR beams** (commonly cited as 38 kHz, ~50 pulses/
second, covering a 180° arc) that the robot discriminates as "left signal" vs. "right signal." The
robot's control loop is simple and robust: if the left-side sensor sees the left beam, steer to
keep it on the left; same for right. This is a closed-loop bearing-only controller, not SLAM or
precision positioning — it only needs to be accurate enough to get the robot's contact strips over
the dock's contact plates, which is a generously sized target
([IR beacon homing reference](https://ozeki.hu/p_6110-homing-to-a-dock-using-an-ir-beacon.html)).

**Docking sequence** (from real teardown/behavioral analysis): the robot beelines toward the
general dock area, swings wide to approach from the front rather than colliding, wiggles
side-to-side to null out the left/right beam signals to zero, then creeps forward along a slight
serpentine path until the contacts touch
([Roomba i7+ Clean Base teardown](https://www.sevarg.net/2019/12/22/roomba-i7-clean-base-teardown/)).
This staged approach — coarse homing, then fine alignment, then a slow final creep — is the part
worth copying regardless of what contact technology you use.

## What a wheeled base like A3's actually needs to add

A3's base is differential-drive + passive casters, 45x45cm footprint, no IR receivers or charging
contacts documented anywhere in its spec sheet. To auto-dock, it needs, at minimum:

1. **Two IR receivers**, front-mounted, angled outward (left/right) to replicate Roomba's
   left/right beam discrimination — cheap commodity parts, the same sensor class used in any IR
   remote-control receiver.
2. **A docking behavior distinct from normal navigation** — this is genuinely new control-loop
   work, not a wrapper around an existing `nori_sdk` call. Nothing in the SDK's method surface
   (checked directly — see `tool_navigation.py`'s method list) exposes docking or charging at all;
   `nori_navigation`'s `navigate_to_waypoint` can get the robot to the *general area* of a saved
   "dock" waypoint, but the final beam-nulling, creep-forward approach is a dedicated closed-loop
   behavior that would need to run against the raw IR sensor readings directly (Pi 5 GPIO/I2C,
   not a `nori_sdk` request/reply round-trip). Flagging this honestly: this is real embedded
   firmware work on top of the existing stack, not something `nori_navigation`/`nori_perception`
   already cover.
3. **Charging contacts** on the chassis, positioned low and either front- or rear-facing depending
   on which way the robot backs/drives onto the dock — the actual design choice below.
4. **A charge-handshake protocol** between the dock and the robot's battery management system —
   real docks include this specifically to avoid overcharging a 432Wh pack and to report charge
   state, not just apply raw voltage
   ([AMR docking design guide](https://www.phihong.com/amr-docking-station-manufacturer-how-to-design-fast-auto-align-charging-docks-for-warehouse-robots/)).

## Pogo pins: the real spec numbers

Pogo pins are the right choice over Roomba-style wiping plates when you want **more contact
points in less space, plus the option of a data/signal line alongside power** (e.g. a serial line
for the charge-handshake protocol above) — the tradeoff is tighter alignment tolerance than a
big flat plate.

- **Current rating**: standard pogo pins handle up to **5A**; high-performance variants reach
  **30A** for fast charging. For reference, a 432Wh pack charged over a leisurely 4–6 hours at
  ~24–48V draws roughly 2–4A average — comfortably inside a single robust pin's rating, with
  headroom to spare using 2–3 parallel pins for redundancy
  ([Pogo Pin Specifications guide](https://promaxpogopin.com/blog/pogo-pin/specifications/)).
- **Spring force**: **30–80 gf** is the right range for a docking-style contact (enough force for
  reliable contact, not so much that repeated docking wears the pins prematurely); above ~120 gf
  increases wear without improving reliability
  ([Alibaba pogo pin buying guide](https://electronics.alibaba.com/buyingguides/pogo-pin-charging-guide-what-you-actually-need-in-2026)).
- **Cycle life**: standard industrial/commercial pogo pins are rated around **100,000 cycles**;
  basic consumer-grade parts start around 10,000. A home robot docking 1–2x/day is 365–730 cycles/
  year — even the cheapest commodity pins last 15+ years at that duty cycle, so cycle life is not
  the constraint here; current rating and mechanical robustness against dust/debris are.
- **Environmental robustness**: in a home with dust and pet hair (a real condition, not an edge
  case), plan for either a **retractable guard** over the contacts when undocked, or **self-
  cleaning wiping action** built into the docking approach itself — both are standard practice in
  commercial AMR dock design, not exotic asks
  ([AMR/warehouse docking design guide](https://www.phihong.com/amr-docking-station-manufacturer-how-to-design-fast-auto-align-charging-docks-for-warehouse-robots/)).

## Mechanical alignment: don't rely on the homing behavior alone

Real docking-station patents converge on the same pattern for a reason: **a funnel-shaped or
V-formation physical lead-in**, independent of the electronic homing, that mechanically corrects
small residual misalignment the IR homing doesn't fully null out. A tapered entry guide lets the
robot self-center even with real positional/angular error at the moment contact is made
([mechanical alignment patent language](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/RE50363)).
For a differential-drive base like A3's, this means: don't just point two pogo pins forward and
hope the IR homing is perfectly accurate — build a physical V-shaped or ramped guide into the dock
that the robot's chassis mechanically rides into during the final creep-forward phase, the same
way Roomba's ramp geometry does the final centering work that its IR beams only get close on.

## Recommended approach for A3 (or a DIY equivalent)

Combine the three proven pieces rather than picking one in isolation:

1. **Roomba-derived two-beam IR homing** for coarse approach (cheap, proven, gets the robot into
   roughly the right position and orientation).
2. **A V-shaped mechanical funnel** on the dock (not on the robot) to do final centering during
   the last few centimeters of the creep-forward approach — this is what makes the next step work
   even with imperfect homing.
3. **A small array of pogo pins (2–4, wired in parallel per rail)** rather than Roomba's flat
   plates, specifically because A3's higher-capacity 432Wh pack and any future data/handshake line
   benefit from pogo pins' higher current-per-contact-area and the option of a signal line
   alongside power — accepting the tighter alignment tolerance the mechanical funnel above exists
   to solve.

## What this costs

Real, DIY-buildable parts, not exotic:

| Component | Estimated cost |
|---|---|
| 2x IR emitter/receiver pairs | $5–15 |
| Pogo pin array (4-pin, high-current) | $10–25 |
| Charge-handshake circuitry (buck/boost + BMS comms) | $20–50 |
| 3D-printed or sheet-metal V-guide + dock housing | $10–30 in materials |
| **Total (parts only)** | **~$50–120** |

This is dramatically cheaper than the fact that it doesn't exist would suggest — the gap in
`REVIEW.md` isn't a hard engineering problem, it's simply a feature Nori Robotics hasn't shipped
yet. Most of the real work is the closed-loop docking *behavior* (the IR-beam-nulling control
loop and the charge-handshake firmware), not the parts.

## References

- Roomba dock IR homing: [IR beacon homing explainer](https://ozeki.hu/p_6110-homing-to-a-dock-using-an-ir-beacon.html) · [Roomba i7+ Clean Base teardown](https://www.sevarg.net/2019/12/22/roomba-i7-clean-base-teardown/) · [Roomba IR sensor troubleshooting](https://piszek.com/2021/01/24/roomba-docking-trouble/)
- Pogo pin specs: [ProMax pogo pin specifications guide](https://promaxpogopin.com/blog/pogo-pin/specifications/) · [Alibaba pogo pin buying guide 2026](https://electronics.alibaba.com/buyingguides/pogo-pin-charging-guide-what-you-actually-need-in-2026) · [magnetic spring-loaded pogo connectors](https://smeconn.com/magnetic-pogo-pin-connector/)
- AMR/mechanical docking design: [Phihong AMR docking design guide](https://www.phihong.com/amr-docking-station-manufacturer-how-to-design-fast-auto-align-charging-docks-for-warehouse-robots/) · [mechanical alignment patent (V-formation/funnel)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/RE50363) · [autonomous robot docking patent](https://patents.google.com/patent/US8461803B2/en)
- [`REVIEW.md`](REVIEW.md) — the gap this doc addresses
- [`docs/ACTUATOR_ALTERNATIVES.md`](ACTUATOR_ALTERNATIVES.md), [`docs/DIY_A3_EQUIVALENT.md`](DIY_A3_EQUIVALENT.md) — companion docs in this same DIY/upgrade series
