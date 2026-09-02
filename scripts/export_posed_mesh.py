"""Export a single, correctly-assembled Nori A3 mesh (GLB + Resonite mesh-JSON) by reading
MuJoCo's own compiled+posed mesh data - reuses the already-verified expanded URDF instead of
reimplementing forward kinematics by hand to merge the 20 separately-authored STL parts.

Run: uv run --with mujoco --with trimesh python scripts/export_posed_mesh.py
Outputs:
  models/nori_description/nori_a3_posed.glb        (Unity import)
  models/nori_description/nori_a3_posed.mesh.json   (ResoniteLink spawn_mesh vertices/submeshes)
"""

from __future__ import annotations

import json
from pathlib import Path

import mujoco
import numpy as np
import trimesh

REPO_ROOT = Path(__file__).resolve().parent.parent
URDF_PATH = REPO_ROOT / "models" / "nori_description" / "urdf" / "nori.expanded.absolute.urdf"
GLB_OUT = REPO_ROOT / "models" / "nori_description" / "nori_a3_posed.glb"
MESHJSON_OUT = REPO_ROOT / "models" / "nori_description" / "nori_a3_posed.mesh.json"


def main() -> None:
    model = mujoco.MjModel.from_xml_path(str(URDF_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)  # resolve every body/geom's world-frame pose at qpos0

    parts: list[trimesh.Trimesh] = []
    for geom_id in range(model.ngeom):
        if model.geom_type[geom_id] != mujoco.mjtGeom.mjGEOM_MESH:
            continue  # skip collision primitives (box/cylinder/sphere) - visual meshes only
        mesh_id = model.geom_dataid[geom_id]
        if mesh_id < 0:
            continue

        v_start = model.mesh_vertadr[mesh_id]
        v_count = model.mesh_vertnum[mesh_id]
        f_start = model.mesh_faceadr[mesh_id]
        f_count = model.mesh_facenum[mesh_id]
        verts_local = model.mesh_vert[v_start : v_start + v_count].copy()
        faces = model.mesh_face[f_start : f_start + f_count].copy()

        pos = data.geom_xpos[geom_id]
        rot = data.geom_xmat[geom_id].reshape(3, 3)
        verts_world = verts_local @ rot.T + pos

        parts.append(trimesh.Trimesh(vertices=verts_world, faces=faces, process=False))

    print(f"Assembled {len(parts)} visual mesh parts from {model.ngeom} total geoms")
    combined = trimesh.util.concatenate(parts)
    combined.remove_unreferenced_vertices()

    GLB_OUT.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(GLB_OUT))
    print(f"Wrote {GLB_OUT} ({GLB_OUT.stat().st_size / 1024:.1f} KB, {len(combined.vertices)} verts, {len(combined.faces)} tris)")

    # Decimate for the Resonite path specifically: 135k triangles is fine for a GLB asset but
    # far too large for a single ResoniteLink spawn_mesh JSON-RPC call (importMeshJSON sends
    # the whole mesh inline, unlike GLB which is a file import) - target ~8k triangles, still
    # clearly recognizable as the robot, small enough for a live scripted spawn.
    target_tris = 8000
    decimated = combined.copy()
    if len(decimated.faces) > target_tris:
        decimated = decimated.simplify_quadric_decimation(face_count=target_tris)
    print(f"Decimated to {len(decimated.faces)} tris for the Resonite mesh-JSON payload")

    # ResoniteLink spawn_mesh schema (verified against resonite-mcp's real spawn_nekomimi
    # script): vertices=[{"position":{x,y,z}}, ...], submeshes=[{"$type":"triangles","triangles":[{vertex0Index,vertex1Index,vertex2Index}, ...]}]
    vertices_json = [{"position": {"x": float(v[0]), "y": float(v[1]), "z": float(v[2])}} for v in decimated.vertices]
    triangles_json = [
        {"vertex0Index": int(f[0]), "vertex1Index": int(f[1]), "vertex2Index": int(f[2])} for f in decimated.faces
    ]
    mesh_json = {"vertices": vertices_json, "submeshes": [{"$type": "triangles", "triangles": triangles_json}]}
    MESHJSON_OUT.write_text(json.dumps(mesh_json), encoding="utf-8")
    print(f"Wrote {MESHJSON_OUT} ({MESHJSON_OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
