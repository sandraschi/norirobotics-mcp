# NORI Printables

3D-printable parts for Nori robots. Everything here is free to use, modify,
and sell under [CC BY 4.0](LICENSE); just credit Nori Robotics.

Three kinds of parts live here:

- **Spares** — replacement parts you can print instead of waiting on us.
- **Custom end effectors** — attachment-point geometry for designing your own
  tools and grippers that mount to the robot.
- **Cosmetics** — covers and trim you can restyle or reprint in your own
  colors and materials.

These files are print-ready exports. They are **not** the robot's design CAD —
for a simulation-ready model of the robot itself, see
[nori_description](https://github.com/Nori-Robotics/nori_description).

## Finding your part

Parts are organized by robot model, one folder per part:

```
<model>/<part-name>/
├── README.md          description, print settings, etc
├── <part-name>.stl    print ready
├── <part-name>.step   edit/design ready
└── images/            preview
```

Every part ships in both formats.

| Model | Parts |
|---|---|
| [A3](a3/) | see folder |
| [L2](l2/) | see folder |

Download an individual file from its folder, or grab everything for a model
from the [latest release](https://github.com/Nori-Robotics/nori-printables/releases).

## Printing

Each part's README lists tested settings. Unless it says otherwise, a safe
default is PLA or PETG, 0.2 mm layers, 3 walls, 15% infill.

## Something broken or missing?

Open an [issue](https://github.com/Nori-Robotics/nori-printables/issues) —
tell us the model and the part. Whether it's a spare that isn't published
yet or an interface you need for a custom attachment: if we can release
it, we will.

## License

Everything in this repository is licensed under
[Creative Commons Attribution 4.0 International](LICENSE) (CC BY 4.0).
You may use, modify, distribute, and sell these parts and derivatives,
commercially or otherwise, as long as you credit Nori Robotics and note
any changes you made.
