# DIY A3-Equivalent: Project Plan

This turns `DIY_A3_EQUIVALENT.md` and `DIY_BASE_STATION.md` into an actual build sheet — bill of
materials with named vendors, Europe vs. Shenzhen sourcing, the tools you actually need, and a
realistic time budget.

**Read this first, honestly: this will not save you much money.** The Match-tier cost estimate
lands at roughly $1,400–2,100 — in or just above Nori A3's own $1,688 — before counting your own
time. This is not a discount project. What it genuinely buys instead: full ownership of the whole
stack, zero cloud dependency, real mechatronics skills, and the chance to end up with something
that matches or exceeds A3's spec on your own terms. Go in for the build, not the savings — it's
a great weekend-and-evenings project precisely because the destination isn't really the point.

## Bill of materials

Match-tier pricing throughout (see `ACTUATOR_ALTERNATIVES.md`/`DIY_A3_EQUIVALENT.md` for the
Exceed-tier QDD-actuator alternative, roughly $1,300 more expensive at the shoulder/elbow joints
alone).

| Component | Qty | Est. price | Best EU source | Shenzhen/import source |
|---|---|---|---|---|
| SO-ARM101 arm kit | 2 | $199 ea. | [Seeed Studio DE warehouse](https://www.seeedstudio.com/SO-101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html) (EU-only shipping) | same listing, CN warehouse also ships worldwide |
| STS3095-class shoulder/elbow upgrade servo | 4 | $70–120 ea. (unconfirmed — verify before ordering) | [RobotShop EU](https://eu.robotshop.com/collections/feetech), [Eckstein Shop](https://eckstein-shop.de/Feetech-STS3215-74V-19kgcm-plastic-case-metal-gear-magnetic-code-dual-shaft-TTL-serial-servo) (Germany) | Seeed Studio CN warehouse |
| Ballscrew linear rail (SFU1605 + NEMA17) | 2–3 | $78 ea. | check local CNC/3D-printer suppliers first (common part) | [eBay listing](https://www.ebay.de/itm/187709575827) ships EU-wide already |
| Differential-drive motors + wheels | 2 sets | $15–30 ea. | any EU robotics/hobby electronics shop | generic — AliExpress |
| Passive casters | 2 | $5–15 ea. | any hardware store | — |
| Raspberry Pi 5 (4–8GB) | 1 | $60–90 | [Mouser Austria](https://www.mouser.at/en/manufacturer/raspberry-pi/) (AT stock, same-day) or [Pimoroni](https://shop.pimoroni.com/en-us/collections/raspberry-pi) (UK) | — (buy EU, no reason not to) |
| USB webcams | 4 | $15–30 ea. | any EU electronics retailer | AliExpress for the cheapest tier |
| **RPLIDAR C1** (not A1 — see note below) | 1 | ~$100–140 | [Génération Robots](https://www.generationrobots.com/en/404200-360-rplidar-c1-slamtec.html) (France, EU) | [AIFITLAB](https://aifitlab.com/products/slamtec-rplidar-c1-lidar) |
| USB dual-mic array + speaker | 1 | $20–50 | any EU electronics retailer | AliExpress |
| 3-finger gripper hardware (per RAMEL-ESPOL BOM) | 2 | $30–60 ea. (mostly printed + 1 servo/hand) | servo from RobotShop EU | — |
| Pogo pin array (base station, 4-pin high-current) | 1 | $10–25 | [SUNMON](https://smeconn.com/pogo-pin-connector/) ships EU | AliExpress, cheaper at this tier |
| IR emitter/receiver pairs (base station) | 2 | $5–15 | any EU electronics retailer | AliExpress |
| Structural: filament, fasteners, wiring, connectors, misc | — | $150–250 | local | mixed |
| **Total (rough)** | | **≈ $1,400–2,000** | | |

**RPLIDAR C1, not A1**: worth being precise here — A3's own official mesh package
(`models/nori_description/meshes/visual/RPLiDarC1.stl`) confirms the real robot uses the **C1**,
and its published specs (12m range, 8–12Hz, 0.72° angular resolution) match `knowledge.py`'s
`NORI_HERO` numbers exactly. The A1 is a fine sensor but is discontinued at some retailers
([The Pi Hut listing shows it as discontinued](https://thepihut.com/products/slamtec-rplidar-a1-360-laser-range-scanner))
— C1 is both the more accurate match and the more current part.

## Sourcing strategy: Europe vs. Shenzhen

**Buy EU-stock where it exists — it does for more of this BOM than you'd expect.** Feetech servos
(RobotShop EU, Eckstein, Seeed's DE warehouse), RobStride actuators (also Seeed DE), Raspberry Pi
5 (Mouser Austria — same-day from an Austrian warehouse), and RPLIDAR C1 (Génération Robots,
France) all have real EU-resident stock. No customs wait, no import paperwork, and the price
premium over direct-China is small at single-unit hobbyist quantities.

**Batch the Shenzhen-only bits into one order, placed early.** Damiao and CubeMars actuators (if
going Exceed-tier), generic pogo pins, IR sensors, and misc connectors are cheapest and sometimes
*only* available via AliExpress/direct China resellers — and shipping runs 2–4 weeks. Per
`ACTUATOR_ALTERNATIVES.md`'s customs section: VAT applies from €0, duty from ~€150 per parcel for
hobbyist-tier purchases — a single consolidated order stays well inside normal personal-import
handling, no broker needed. Place this order in week 1 so it's not the thing you're waiting on at
the end.

## Necessary maker tools

- **3D printer**, or a membership at a local makerspace. Vienna has [Happylab](https://www.happylab.at/en_vie) —
  a real, active 900m² makerspace with 3D printers, laser cutters, CNC mills, and electronics
  workstations; membership plus a short machine-training session is required before use. Check
  [happylab.at](https://www.happylab.at/en_vie) directly for current membership/day rates — not
  found in this research pass, and worth confirming before counting on it in your timeline.
- **Computer running Blender** (`blender-mcp`) and a parametric CAD tool (`qcad-mcp` / FreeCAD) —
  for the mesh-repair-and-reconstruct pass in `DIY_A3_EQUIVALENT.md`, done once before any
  printing starts.
- **Digital calipers** — verify every repaired/reconstructed part's critical dimensions against
  the URDF's real measured joint transforms before committing to a full print run.
- **Soldering iron, solder, flux**, basic through-hole/SMD soldering skill.
- **Multimeter** — verify voltage/continuity before powering any actuator for the first time.
  Non-negotiable before wiring a $70–260 actuator to anything.
- **Metric hex key set** — servo horns and most robotics fasteners are metric.
- **Wire strippers/crimpers** + a basic JST/XT-connector kit.
- **A bench PSU, or at minimum the ability to power and test one actuator at a time in
  isolation** before final wiring — the cheapest insurance against a wiring mistake frying a
  shoulder-joint actuator on day one.

## Build phases and time estimates

| Phase | Estimated time | Notes |
|---|---|---|
| Mesh repair + CAD reconstruction (`blender-mcp`/`qcad-mcp`) | 8–15 hrs | Once, up front — every printed part depends on this being right |
| Sourcing/ordering wait | 1–4 weeks calendar time | Not active build time — order Shenzhen-only parts in week 1 |
| 3D printing all structural parts | 20–40 hrs print time (mostly unattended) + 4–8 hrs post-processing | Budget for at least one reprint of a part that doesn't fit first try |
| Arm assembly (x2) | 6–10 hrs | Including servo calibration per arm |
| Telescoping lift build | 6–12 hrs | Ballscrew-rail option is faster to get right than a scratch-built nested-tube column |
| Base assembly | 3–6 hrs | Differential drive is the simpler, faster option vs. holonomic |
| Electronics integration (compute, sensors, wiring) | 8–15 hrs | Where most first-build debugging time actually goes |
| Software bring-up (LeRobot calibration, actuator-protection layer) | 10–20 hrs | The actuator-protection layer specifically is new work, not a config file |
| Base station build (if included) | 8–15 hrs | Per `DIY_BASE_STATION.md` — IR homing + pogo pins + mechanical V-guide |
| Integration/debugging buffer | 10–20 hrs | Always underestimated — budget it explicitly rather than being surprised by it |
| **Total active hands-on time** | **≈ 80–150 hrs** | Realistic for a first-time build in this class, spread over several weekends |

## The honest bottom line

Total spend lands close to or somewhat above what A3 costs assembled, plus 80–150 hours of your
own time, plus no warranty and no professional integration pass. What you get instead: a robot
you understand completely, that runs with zero cloud dependency, that you can rebuild or upgrade
piece by piece, and the actual experience of building it — which, if you're the kind of person
reading a document like this one, is the real deliverable. Great fun is a legitimate project
justification. Just don't budget it as a savings plan.

## References

- [`DIY_A3_EQUIVALENT.md`](DIY_A3_EQUIVALENT.md) — the full engineering design this BOM builds
- [`DIY_BASE_STATION.md`](DIY_BASE_STATION.md) — the optional charging-dock addition
- [`ACTUATOR_ALTERNATIVES.md`](ACTUATOR_ALTERNATIVES.md) — actuator vendor comparison and PRC customs detail
- [RPLIDAR C1 @ Slamtec](https://www.slamtec.com/en/c1) · [@ Génération Robots](https://www.generationrobots.com/en/404200-360-rplidar-c1-slamtec.html)
- [Happylab Vienna](https://www.happylab.at/en_vie)
- [Mouser Austria — Raspberry Pi](https://www.mouser.at/en/manufacturer/raspberry-pi/)
