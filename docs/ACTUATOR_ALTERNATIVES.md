# Feetech vs. the Alternatives: Actuator Upgrade Paths for the Nori A3

This is a survey, not a spec — it exists to make the actuator-upgrade question in
[`docs/REVIEW.md`](REVIEW.md) and `nori_info(operation="actuator_upgrade")` concrete: what would
you actually buy, what would it cost, and what would you get for it. No specific BOM
recommendation is made — see the Caveat section. The eventual home for any real implementation
is [`universal-actuator-mcp`](https://github.com/sandraschi/universal-actuator-mcp), per this
repo's existing `FLEET_PEERS` note.

## The baseline: what Nori A3 actually ships with

Feetech's STS-series bus servos — RC-hobbyist lineage, position-controlled, TTL serial, a single
magnetic encoder, and a high-reduction internal gearbox (1:345 on the STS3215):

| Model | Stall torque | ≈ Nm | Price (single unit) |
|---|---|---|---|
| STS3215 | 30 kg·cm | 2.9 Nm | ~$16–24 ([WowRobo](https://shop.wowrobo.com/products/feetech-sts3215-servo-12v-30kg-high-torque-servo-for-so-arm100), [servodatabase](https://servodatabase.com/servo/feetech/sts3215)) |
| STS3250 | 50 kg·cm | 4.9 Nm | ~$48–55 ([servodatabase](https://servodatabase.com/servo/feetech/sts3250)) |
| STS3095 | 95 kg·cm | 9.3 Nm | not found in this pass — this is Nori A3's shoulder/lift axis per the existing `ACTUATOR_UPGRADE_NOTES` in [`knowledge.py`](../src/norirobotics_mcp/knowledge.py) |

This is genuinely commodity pricing — a single STS3215 costs less than a fast-food meal. That's
the whole point of the choice: at $1,688 for a complete 19-DOF robot, every joint's actuator
budget is a rounding error compared to what a single research-grade actuator alone would cost.

**The real limitation isn't the torque ceiling, it's the gear ratio.** A 1:345 reduction means
motor-side current bears almost no clean relationship to output-side torque — friction and
backlash in that much gearing swamp the signal. Nori's own workaround (sensorless force sensing
via the servo's `Present_Current` register, documented in `HOME_ROBOT_PARADIGM.md`) is a genuine,
clever software compromise for exactly this reason — it's approximating what a lower-ratio
actuator would give you for free. That framing matters for everything below.

## Torque vs. speed: why a home robot's needs genuinely differ from a dogbot's

This is a real, physics-level distinction, not just a cost-cutting story. Actuator torque and
speed trade off directly against each other for a given motor size and power budget — you cannot
maximize both without a bigger, heavier, more expensive motor
([CubeMars' own selection guide](https://www.cubemars.com/robotic-actuator-and-servo-motor-selection-guide.html)
makes this the first design question).

A legged robot's actuators live in **two very different regimes within the same gait cycle**: a
swing-phase leg must move fast and light through the air, while a stance-phase leg must support
multiples of body weight — vertical ground-reaction forces can hit **3x body weight** — with very
little speed at all. These two requirements are often an order of magnitude apart, which is why
quadruped/humanoid actuator design is a genuinely harder, more expensive problem, and why some
research platforms use two-speed transmissions or variable-ratio drives specifically to avoid
compromising both regimes at once
([arXiv:2405.16652](https://arxiv.org/pdf/2405.16652), [arXiv:2203.00644](https://arxiv.org/pdf/2203.00644)).

**A home manipulator arm doesn't have this problem.** Reaching for a cup, closing a drawer,
lifting a laundry item onto a shelf — these are quasi-static tasks. Nothing about them needs a
Unitree Go2's leg-swing speed; they need enough torque to hold a pose against gravity and payload,
precisely and quietly. This is the actual engineering justification behind the user's framing:
**a home robot can spend its actuator budget almost entirely on torque and precision, buying real
capability upgrade headroom that a running dogbot's actuators can't afford to give up for speed.**

## The QDD alternative: why it gives you force feedback almost for free

Quasi-direct-drive (QDD) actuators use a **low reduction ratio** (single digits up to ~10:1,
vs. Feetech's 1:345) between a purpose-built BLDC motor and the output. At that ratio, gearbox
friction is low enough that **motor current genuinely correlates with output torque** — Field-
Oriented Control (FOC) current sensing gives real, usable torque estimation with no added
sensor, entirely different from Feetech's high-ratio situation where the same trick barely works.
A recent survey on legged-robot actuator sensing states this plainly: current sensing is "good
enough" for QDD specifically *because* of the low gear ratio, while high-reduction gears (strain
wave / harmonic drives) need a dedicated strain-gauge torque sensor at real added cost and
complexity to get the same signal ([arXiv:2510.10843](https://arxiv.org/html/2510.10843v1),
[Frontiers in Robotics and AI](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1416360/full)).

That's the actual headline reason to consider a QDD swap over "more Feetech" — it isn't only
about a higher torque number, it's that force feedback quality improves structurally, for free,
as a side effect of the gearing choice.

## Vendor-by-vendor comparison

All figures below are as published by the vendor or a reseller at time of writing — treat as a
starting point for direct verification, not a locked BOM.

| Vendor | Model | Rated torque | Peak torque | Price | Notes |
|---|---|---|---|---|---|
| **Feetech** (baseline) | STS3095 | — | 9.3 Nm | n/a | What Nori A3 ships with |
| **CubeMars** ([AK series](https://www.cubemars.com/categorys/ak-series-robotic-actuator)) | AK80-9 v3.0 | ~9 Nm | 22 Nm | not found | Also sold under the **T-Motor** name in some listings ([MAB Robotics](https://www.mabrobotics.pl/product-page/ak80-6)) — confirm which brand/warranty applies before ordering |
| **CubeMars** | AK80-64 | 48 Nm | 120 Nm | not found | [product page](https://www.cubemars.com/product/ak80-64-kv80-robotic-actuator.html) |
| **CubeMars AKE** (QDD variant) | AKE60-8 | — | — | not found | ~9 arcmin backlash, up to 46 Nm/kg torque density ([AKE line](https://www.cubemars.com/ake-qdd-motors.html)) |
| **MyActuator** ([RMD-X series](https://www.dingsmotionusa.com/rmd-x-series)) | RMD-X6 | 3.5 Nm | ~7 Nm | not found | Wide range across the line, 3–400 Nm depending on model ([RobotShop listings](https://www.robotshop.com/products/myactuator-rmd-x6-16-rs485)) |
| **Damiao** ([DM-J series](https://www.roboticscenter.ai/wiki/damiao-motors)) | DM-J4310-2EC | 7 Nm | — | **$116** | Used in the open-source [OpenArm](https://store.foxtech.com/damiao-joint-motor-system-for-openarm-open-source-robot-arm/) robot arm project |
| **Damiao** | DM-J4340-2EC | 27 Nm | — | not found (DM-J6006 at this tier: $214) | |
| **Damiao** | DM-J8009P-2EC | 40 Nm | — | **$398** | |
| **Xiaomi CyberGear** | Micromotor | 1.3–40 Nm (variant-dependent) | 4.1–120 Nm | $136–799 | **Marked EOL** ([OpenELAB product page](https://openelab.io/products/xiaomi-cybergear-micromotor-intelligent-motor)) — do not plan a BOM around this one |
| **RobStride** | RobStride 00 | — | 14 Nm | not found | [Seeed Studio](https://www.seeedstudio.com/Robostride-00-Actuator-p-6664.html) |
| **RobStride** | RobStride 01/02 | 6 Nm | 17 Nm | ~$260-class | Dual 14-bit magnetic encoders, IP52, 405g ([OpenELAB comparison guide](https://openelab.io/blogs/learn/complete-guide-to-robstride-qdd-motors-model-comparison-and-selection)) |
| **RobStride** | RobStride 04 | — | 120 Nm | **from $260** | Explicitly marketed as **"Unitree-compatible"** ([product listing](https://rcdrone.top/products/robstride-02-qdd-17n-m-integrated-actuator-module-7-75-1-ratio-dual-14-bit-magnetic-encoders-48v-405g-foc-drive-for-robotics)) |

**Reading this table honestly**: a Damiao or RobStride joint in the 17–27 Nm class costs roughly
$120–260 — call it 5–15x a single Feetech STS3095, for 2–3x the torque **plus** genuinely better
force feedback (see above). That's a real, defensible trade for a shoulder or lift axis. It is
not remotely a drop-in swap — different voltage (24–48V vs. Feetech's 12V), different
communication protocol (CAN/EtherCAT vs. TTL serial), different mounting, and a firmware/protocol
integration effort on top.

## So the "advanced motor" isn't the moat either — it's already commodity

It's tempting to read the table above as "the big humanoid/quadruped companies have secret motor
technology, and buying a CubeMars/RobStride/Damiao unit gets you a taste of it." **The evidence in
this doc actually argues the opposite.** These are independent vendors selling genuine QDD
actuators with real integrated force feedback, at retail, to anyone, for $78–400/unit — and
RobStride markets its top-end unit explicitly as **"Unitree-compatible."** A third party can only
credibly sell into that positioning if the actual hardware gap between "what a large humanoid/
quadruped maker puts in its product" and "what anyone can order this week" is small. If the
actuator itself were the real moat, that market wouldn't exist in this form.

What's left, once the actuator technology itself is commodity: **controls software** (the gait/
manipulation tuning that turns "has a QDD actuator" into "can backflip" or "can fold a shirt
reliably" — this is where real engineering effort still concentrates, and it's the one thing you
can't order from Shenzhen), **manufacturing scale and vertical integration** (owning your own
actuator fab is a cost/supply-security advantage over buying at retail markup, not a technology
one), and **system-level reliability at volume** (thermal management, QA, failure rates across
thousands of units — a capital-intensive, boring problem unrelated to any single component being
secret). Nori A3 illustrates the same pattern in miniature at a smaller price point: it didn't
even reach for the commodity QDD tier — it used cheap RC servos and pushed the gap to software
(current-sensing force estimation, actuator-protection) instead. Same move, smaller scale: when a
hardware differentiator dissolves, the remaining leverage is software, not a better motor.

## The "use Unitree's own motors" idea, specifically

Unitree does sell some standalone actuators — the `GO-M8010-6` (an older Go1-era motor) is
**$369** direct from the [official Unitree Shop](https://shop.unitree.com/products/go1-motor).
But the joint motors on their current quadrupeds are a different class entirely: Go2's largest
leg joint peaks around **345 Nm** ([teardown analysis](https://www.simplexitypd.com/blog/unitree-go2-motor-teardown/))
— built for a robot that runs, jumps, and absorbs its own body weight landing on one leg. That's
roughly 3x even RobStride's top 120 Nm actuator, wildly oversized (and almost certainly wildly
over-budget) for a 55cm-reach, 1.5kg-payload arm joint on a stationary-base manipulator.

The teardown source makes the more useful point directly: **the value isn't literally bolting a
leg motor onto an arm — it's that these integrated joints, once torn down, reveal an underlying
motor/gearbox/driver combination that has equivalent, independently-sourceable parts** at a
fraction of the "complete Unitree spare part" price. RobStride and CubeMars already productize
this observation — RobStride's own marketing explicitly targets Unitree-actuator-class buyers
looking for a compatible alternative. Buying "the Unitree motor" isn't really the move; buying
one of the QDD vendors above, sized to the *arm's* actual torque need rather than a *quadruped
stance leg's*, is the practical version of the same idea.

## Direct import from China (PRC) — what it actually takes

Every vendor above ships from China. Two very different tiers exist:

- **Hobbyist/single-few-unit retail** (AliExpress, RobotShop, Seeed Studio, OpenELAB, Foxtech —
  i.e., every link in the table above): this is already how the open-source robotics community
  buys these parts. VAT applies from €0 on parcels into the EU, and customs duty kicks in above
  roughly **€150** per the [2026 EU import guide](https://www.parcel-guide.eu/guides/customs-and-vat-importing-from-china/)
  — a single actuator or a handful of them stays well inside normal personal-import handling, no
  broker needed.
- **B2B wholesale** (Alibaba, 1688.com, direct factory contact): only worth it at volumes this
  project doesn't need. EU duty on robotic goods generally runs **0–6.5%** depending on exact
  classification, but a real import at this tier needs a customs broker, correct HS-code
  classification (spare actuators can be classified differently — and taxed differently — than a
  "complete robot"), CE/FCC documentation, and clear Incoterms (FOB vs. CIF changes who's on the
  hook for what) — see the [EVS Robot customs guide](https://www.evsrobot.com/import-industrial-robots-from-china-shipping-customs-guide.html)
  and [Basenton's shipping guide](https://www.basenton.com/guide-to-importing-and-shipping-robots-from-china/).

**Practical read for a Nori A3 upgrade at joint-count quantities (2–8 actuators)**: buy through
the same hobbyist-tier resellers everyone in this table already uses. The price difference
against a "proper" B2B import is small at this volume, and it skips the broker/HS-code/customs
overhead entirely. The one thing worth double-checking regardless of channel: **confirm voltage
explicitly** — these actuators run 24–48V against Nori's Feetech bus, and a mismatch risks the
controller, not just the motor.

## What an actual upgrade path would look like

Per the existing (unchanged) conclusion in `ACTUATOR_UPGRADE_NOTES`: the shoulder/lift axes are
the most plausible target, since STS3095's 9.3 Nm ceiling is closest to being load-limited for a
1.5kg-payload, 55cm-reach arm. A QDD swap there is *tractable* — not easy, but not exotic —
specifically because Nori's actuator-protection layer is already open-sourced and operates at the
protocol level in a torque/stall-agnostic way, rather than hard-coding assumptions about
Feetech's specific current-sensing behavior. A Damiao DM-J4340 (27 Nm) or a RobStride 01/02-class
actuator (17 Nm) would roughly 2–3x the torque ceiling at that joint, with materially better
native force feedback, for a few hundred dollars per joint in parts alone.

The gripper and wrist axes are almost certainly **not** worth swapping — they're low-torque,
low-mass, and Feetech's cheap-and-light profile is already the right fit there. This is a
targeted upgrade for one or two joints, not a wholesale actuator replacement.

## Caveat

**No specific BOM or part-number recommendation is made here** — this is a sourced survey, not
fleet advice. A real upgrade needs a backdrivability/mounting/protocol-integration pass this
research didn't do, and every price above should be re-verified directly before ordering (single
web-search-pass pricing, not a live quote). See `universal-actuator-mcp` for where that next pass
belongs.

## Links and references

- Feetech: [STS3215 @ WowRobo](https://shop.wowrobo.com/products/feetech-sts3215-servo-12v-30kg-high-torque-servo-for-so-arm100) · [STS3215 @ servodatabase](https://servodatabase.com/servo/feetech/sts3215) · [STS3250 @ servodatabase](https://servodatabase.com/servo/feetech/sts3250)
- CubeMars: [AK series](https://www.cubemars.com/categorys/ak-series-robotic-actuator) · [AKE QDD line](https://www.cubemars.com/ake-qdd-motors.html) · [AK80-64](https://www.cubemars.com/product/ak80-64-kv80-robotic-actuator.html) · [selection guide](https://www.cubemars.com/robotic-actuator-and-servo-motor-selection-guide.html) · [AK80-6 @ MAB Robotics (T-Motor branding)](https://www.mabrobotics.pl/product-page/ak80-6)
- MyActuator: [RMD-X series @ Dings Motion USA](https://www.dingsmotionusa.com/rmd-x-series) · [RMD-X6 @ RobotShop](https://www.robotshop.com/products/myactuator-rmd-x6-16-rs485)
- Damiao: [reference wiki @ RoboticsCenter](https://www.roboticscenter.ai/wiki/damiao-motors) · [OpenArm joint motor system @ Foxtech](https://store.foxtech.com/damiao-joint-motor-system-for-openarm-open-source-robot-arm/)
- Xiaomi CyberGear: [product page (EOL) @ OpenELAB](https://openelab.io/products/xiaomi-cybergear-micromotor-intelligent-motor) · [overview @ OpenELAB](https://openelab.io/blogs/learn/what-is-xiaomi-cybergear-micromotor)
- RobStride: [model comparison guide @ OpenELAB](https://openelab.io/blogs/learn/complete-guide-to-robstride-qdd-motors-model-comparison-and-selection) · [RobStride 00 @ Seeed Studio](https://www.seeedstudio.com/Robostride-00-Actuator-p-6664.html)
- Unitree: [GO-M8010-6 @ official shop](https://shop.unitree.com/products/go1-motor) · [Go2 motor teardown @ Simplexity](https://www.simplexitypd.com/blog/unitree-go2-motor-teardown/)
- Torque sensing / QDD force feedback: [arXiv:2510.10843](https://arxiv.org/html/2510.10843v1) · [Frontiers in Robotics and AI](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1416360/full)
- Torque vs. speed tradeoff in legged actuators: [arXiv:2405.16652 (two-speed actuator)](https://arxiv.org/pdf/2405.16652) · [arXiv:2203.00644 (Tello Leg)](https://arxiv.org/pdf/2203.00644)
- China import / customs: [2026 EU customs & VAT guide](https://www.parcel-guide.eu/guides/customs-and-vat-importing-from-china/) · [EVS Robot customs guide](https://www.evsrobot.com/import-industrial-robots-from-china-shipping-customs-guide.html) · [Basenton shipping guide](https://www.basenton.com/guide-to-importing-and-shipping-robots-from-china/)
