# Nori A3 Description

A URDF/xacro description of the **Nori A3** mobile manipulator, for simulation
and visualisation. Loads in Isaac Sim, MuJoCo, Gazebo, or anything that reads
URDF.

- Try it in a browser, nothing to install: <https://lab.norirobotics.com/nori/model>
- Docs: <https://docs.norirobotics.com/guide/a3>


## Layout

```
urdf/              the model (xacro; nori.urdf.xacro is the top level)
config/            per-link mass
meshes/visual/     simplified visual meshes
ros2_control/      hardware interface description
launch/  rviz/     visualisation
```

Expand it with `xacro urdf/nori.urdf.xacro`.

## Before you build on it

Read `NOTICE`. It states plainly what is measured and what is not — kinematics
are verified against hardware, total mass is ~8.7% light, inertia is
approximate, the lift's joint limit is an operating ceiling rather than its
stroke, and the torso/neck/head shapes are placeholders.

Three joints use `mimic` (the lift's middle stage and both geared grippers) and
are the most common import casualty. If the lift's middle section does not move
at half the top's rate, or a gripper's second finger stays still while the first
closes, the mimic did not survive the import.

## License

CC BY-NC-SA 4.0 — free for research and simulation, share-alike, **not for
commercial use**. See `LICENSE`. Commercial enquiries: info@norirobotics.com
