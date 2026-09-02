# Vendored Nori A3 hardware assets — attribution

Both directories here are vendored verbatim (git history stripped) from Nori Robotics' own
public GitHub org, fetched 2026-09-02.

## `nori_description/`

- Source: https://github.com/Nori-Robotics/nori_description (main branch, 2026-09-02)
- License: **CC BY-NC-SA 4.0** (non-commercial, share-alike) — see `nori_description/LICENSE`,
  `nori_description/LICENSES/LICENSE-CC-BY-NC-SA-4.0.txt`
- Copyright 2026 Nori Robotics Inc.
- Contents: ROS 2 URDF/xacro description (`urdf/`), 20 STL visual meshes per-link
  (`meshes/visual/`), inertial parameter estimates (`config/`), ros2_control hardware
  interface xacros, RViz config, launch files.
- **Read `nori_description/NOTICE` before using this for anything beyond
  simulation/visualization** — Nori Robotics' own notice states plainly: kinematics
  (joint axes/limits/link transforms) are measured and verified against hardware, but
  inertial properties are approximate, collision geometry is deliberately coarse, total
  mass is ~8.93% light (scale by 1.121 for real total), and **the RPLiDAR C1 mesh is a
  primitive stand-in, not Slamtec's real geometry** (third-party mesh, not redistributed).
  Not manufacturing data, not for safety-critical use.

## `nori-printables/`

- Source: https://github.com/Nori-Robotics/nori-printables (main branch, 2026-09-02)
- License: **CC BY 4.0** (attribution, commercial use OK) — see `nori-printables/LICENSE`
- Contents: print-ready STL + design-ready STEP files for the A3 (and L2), organized as
  spares (replacement parts), custom end-effector attachment geometry, and cosmetic
  covers/trim. Distributed as print-ready exports, not the robot's original design CAD.

## Why these are vendored here (not fetched live)

`norirobotics-mcp` is the canonical fleet integration point for Nori A3 — matching the
existing pattern of vendoring hardware CAD directly in-repo (see `yahboom-mcp`'s
`raspbot_v2_step.STEP`). Re-fetch periodically to pick up upstream corrections; check
`git log` on the upstream repos before assuming this copy is current.
