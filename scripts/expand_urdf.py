"""Expand nori_description's xacro into a flat, non-ROS-dependent URDF.

The vendored xacro uses two ROS-specific things no non-ROS consumer (MuJoCo, Isaac Sim,
plain urdfpy/trimesh) can resolve on its own:
  1. `$(find nori_description)` — ament package-path substitution (needs a real ROS 2
     ament index; we don't have one, so we pre-substitute it with this repo's local path).
  2. `package://nori_description/...` mesh URIs — replaced post-expansion with paths
     relative to the output URDF's own directory, so `<mesh filename="meshes/visual/...">`
     just works for tools that resolve mesh paths relative to the URDF file.

Run: uv run --with xacro python scripts/expand_urdf.py
Output: models/nori_description/urdf/nori.expanded.urdf (generated — not the vendored source)
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESC_DIR = REPO_ROOT / "models" / "nori_description"
XACRO_PATH = DESC_DIR / "urdf" / "nori.urdf.xacro"
OUT_PATH = DESC_DIR / "urdf" / "nori.expanded.urdf"
# Absolute-mesh-path variant for consumers OUTSIDE this repo (e.g. mujoco-mcp's load_model,
# which copies only the single model file flat into its own depot - relative "../meshes/"
# paths would break the moment the file leaves this repo's urdf/ directory).
OUT_ABS_PATH = DESC_DIR / "urdf" / "nori.expanded.absolute.urdf"


def main() -> None:
    import xacro

    # inertial.xacro's $(find nori_description) needs a real ament index we don't have -
    # patch the one xacro file that uses it to point at our local vendored copy instead.
    inertial_xacro = DESC_DIR / "urdf" / "inertial.xacro"
    original = inertial_xacro.read_text(encoding="utf-8")
    patched = original.replace(
        "$(find nori_description)",
        DESC_DIR.as_posix(),
    )
    if patched == original:
        raise RuntimeError("Expected '$(find nori_description)' in inertial.xacro - source may have changed")
    inertial_xacro.write_text(patched, encoding="utf-8")

    try:
        doc = xacro.process_file(str(XACRO_PATH))
        xml = doc.toprettyxml(indent="  ")
        # MuJoCo's URDF importer drops <visual> mesh geometry by default, keeping only
        # <collision> primitives - confirmed empirically (a <visual><mesh> + <collision><box>
        # on the same link compiles to nmesh=0, geom_type=box only) unless told otherwise via
        # this MuJoCo-specific extension block embedded in the URDF root. strippath="false"
        # keeps our already-absolute mesh paths intact instead of stripping to basename.
        marker = '<robot name="nori">'
        if marker not in xml:
            raise RuntimeError(f"Expected {marker!r} in expanded xacro output - root tag format changed")
        xml = xml.replace(
            marker,
            marker + '\n  <mujoco><compiler discardvisual="false" strippath="false"/></mujoco>',
            1,
        )
    finally:
        # Always restore the vendored source untouched, even if expansion fails.
        inertial_xacro.write_text(original, encoding="utf-8")

    # package://nori_description/X -> X (relative to this URDF's own directory, which is
    # models/nori_description/urdf/ - meshes live one level up at models/nori_description/meshes/).
    xml_relative = re.sub(r"package://nori_description/", "../", xml)
    OUT_PATH.write_text(xml_relative, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(xml_relative)} bytes)")

    # Absolute variant: package://nori_description/X -> <repo>/models/nori_description/X as a
    # plain filesystem path, not a file:// URI (MuJoCo's URDF mesh loader treats filename as a
    # path to resolve, not a URI to parse) - see scripts/expand_urdf.py verification note below.
    mesh_root = DESC_DIR.resolve().as_posix()
    xml_absolute = re.sub(r"package://nori_description/", f"{mesh_root}/", xml)
    OUT_ABS_PATH.write_text(xml_absolute, encoding="utf-8")
    print(f"Wrote {OUT_ABS_PATH} ({len(xml_absolute)} bytes)")


if __name__ == "__main__":
    main()
