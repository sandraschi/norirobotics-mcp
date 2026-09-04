"""Export the Nori A3 mesh from MuJoCo's own compiled+posed model data - reuses the
already-verified expanded URDF instead of reimplementing forward kinematics by hand.

Two outputs:
  models/nori_description/nori_a3_posed.glb        flattened, world-posed (Unity import,
                                                     Resonite mesh-JSON source) - single mesh,
                                                     not animatable.
  models/nori_description/nori_a3_rig.glb          per-body node hierarchy at rest pose
                                                     (qpos0) - same visual result as the
                                                     flattened GLB, but each MuJoCo body is a
                                                     separate named glTF node, so a viewer can
                                                     rotate individual joints (e.g. for a demo
                                                     animation) instead of only displaying a
                                                     static blob.
  models/nori_description/nori_a3_posed.mesh.json   decimated flattened mesh, ResoniteLink
                                                     spawn_mesh vertices/submeshes schema.

Visual-vs-collision geoms: MuJoCo's URDF importer keeps BOTH a <visual> and a <collision>
geom per primitive shape (e.g. torso's box, the lift column's boxes). Only the visual copy has
contype=0/conaffinity=0 - filtering on that (not on geom type) is required, or every collision
box/cylinder doubles up and the torso/head/lift-column boxes (which have no <mesh> at all, so
type-only filtering silently dropped them) go missing. Found by comparing the URDF's authored
link list against what a type==MESH-only filter actually rendered - torso_shell_link,
head_link, and the three lift_*_link boxes are visual-only primitives.

Run: uv run --with mujoco --with trimesh --with fast-simplification --with scipy python scripts/export_posed_mesh.py
"""

from __future__ import annotations

import json
from pathlib import Path

import mujoco
import numpy as np
import trimesh
import trimesh.transformations as tf

# MuJoCo/URDF/ROS are Z-up; glTF (and everything that reads it - Three.js, Unity, Resonite's
# FrooxEngine) is Y-up. trimesh does NOT convert this on export (checked: no axis-handling
# code anywhere in trimesh.exchange.gltf) - it writes coordinates through verbatim. Applied
# once, globally, at the very end via Scene/Trimesh.apply_transform rather than baked into
# every individual geom/body transform. A -90deg rotation about X: (x,y,z) -> (x,z,-y).
ZUP_TO_YUP = np.array(
    [
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, -1, 0, 0],
        [0, 0, 0, 1],
    ],
    dtype=float,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
URDF_PATH = REPO_ROOT / "models" / "nori_description" / "urdf" / "nori.expanded.absolute.urdf"
FLAT_GLB_OUT = REPO_ROOT / "models" / "nori_description" / "nori_a3_posed.glb"
RIG_GLB_OUT = REPO_ROOT / "models" / "nori_description" / "nori_a3_rig.glb"
MESHJSON_OUT = REPO_ROOT / "models" / "nori_description" / "nori_a3_posed.mesh.json"


def is_visual_geom(model: mujoco.MjModel, gid: int) -> bool:
    """Visual-only copy: MuJoCo's URDF importer gives collision geoms contype=1/conaffinity=1."""
    return model.geom_contype[gid] == 0 and model.geom_conaffinity[gid] == 0


def geom_local_mesh(model: mujoco.MjModel, gid: int) -> trimesh.Trimesh | None:
    """Build the geom's own shape, centered at its local origin, in its own local frame -
    caller applies whatever transform (world pose, or body-local pose) is needed."""
    gtype = model.geom_type[gid]
    size = model.geom_size[gid]

    if gtype == mujoco.mjtGeom.mjGEOM_MESH:
        mesh_id = model.geom_dataid[gid]
        if mesh_id < 0:
            return None
        v_start = model.mesh_vertadr[mesh_id]
        v_count = model.mesh_vertnum[mesh_id]
        f_start = model.mesh_faceadr[mesh_id]
        f_count = model.mesh_facenum[mesh_id]
        verts = model.mesh_vert[v_start : v_start + v_count].copy()
        faces = model.mesh_face[f_start : f_start + f_count].copy()
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    elif gtype == mujoco.mjtGeom.mjGEOM_BOX:
        mesh = trimesh.creation.box(extents=2 * size)
    elif gtype == mujoco.mjtGeom.mjGEOM_CYLINDER:
        mesh = trimesh.creation.cylinder(radius=size[0], height=2 * size[1], sections=24)
    elif gtype == mujoco.mjtGeom.mjGEOM_SPHERE:
        mesh = trimesh.creation.icosphere(radius=size[0], subdivisions=2)
    else:
        return None

    rgba = (model.geom_rgba[gid] * 255).astype(np.uint8)
    mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=np.tile(rgba, (len(mesh.vertices), 1)))
    return mesh


def body_local_matrix(model: mujoco.MjModel, body_id: int) -> np.ndarray:
    """Body's pose relative to its parent at qpos0 - the rest-pose local transform for the
    glTF node hierarchy. MuJoCo quaternions are (w, x, y, z), matching trimesh's convention."""
    mat = tf.quaternion_matrix(model.body_quat[body_id])
    mat[:3, 3] = model.body_pos[body_id]
    return mat


def geom_local_matrix(model: mujoco.MjModel, gid: int) -> np.ndarray:
    mat = tf.quaternion_matrix(model.geom_quat[gid])
    mat[:3, 3] = model.geom_pos[gid]
    return mat


# qpos0 (all-zero) is a kinematic reference pose, not a natural resting one - both arms end
# up fully extended straight out to the sides (documented in nori_feetech.ros2_control.xacro:
# "the all-zeros arm pose is exactly rank-deficient... the arm is fully extended"). That
# xacro also gives the real READY pose it uses instead (same values, both arms, mirrored) -
# use that for a recognizable static render instead of the T-pose.
READY_POSE = {
    "shoulder_pitch_joint": 2.35,
    "shoulder_roll_joint": -0.60,
    "bicep_yaw_joint": 1.75,
    "elbow_pitch_joint": 1.20,
    "forearm_yaw_joint": 1.55,
    "wrist_pitch_joint": 0.50,
    "wrist_roll_joint": -0.90,
}


def apply_ready_pose(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    for side in ("left", "right"):
        for suffix, angle in READY_POSE.items():
            joint_name = f"{side}_{suffix}"
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
            if jid < 0:
                print(f"WARNING: joint {joint_name!r} not found - skipping ready-pose value")
                continue
            data.qpos[model.jnt_qposadr[jid]] = angle


def main() -> None:
    model = mujoco.MjModel.from_xml_path(str(URDF_PATH))
    data = mujoco.MjData(model)
    apply_ready_pose(model, data)
    mujoco.mj_forward(model, data)  # resolve every body/geom's world-frame pose at the ready pose

    visual_gids = [gid for gid in range(model.ngeom) if is_visual_geom(model, gid)]
    print(f"{len(visual_gids)} visual geoms out of {model.ngeom} total (rest are collision copies)")

    # ---- Flattened, world-posed export (Unity / Resonite source) ----
    # At the ready pose (non-zero joint angles) the right arm's own kinematic solve does NOT
    # mirror the left arm cleanly - confirmed empirically: even negating every right-side
    # joint angle only partially corrects it (elbow Z matched, X/wrist still diverged), so
    # this isn't a simple uniform sign flip and the actual per-joint origin convention
    # responsible hasn't been fully reverse-engineered. Sidestep it for the static render:
    # skip the right arm's own geometry entirely and mirror the (correctly-posed) left arm
    # across the lateral plane instead - guarantees bilateral symmetry regardless of what's
    # actually going on in the right chain's origins. Does not affect the rig export (real
    # per-body kinematics, needed as-is for animation) or the Wave demo (left-arm only).
    RIGHT_ARM_BODIES = {
        "right_shoulder_pitch_link",
        "right_shoulder_roll_link",
        "right_bicep_yaw_link",
        "right_elbow_pitch_link",
        "right_forearm_yaw_link",
        "right_wrist_pitch_link",
        "right_wrist_roll_link",
        "right_gripper_link",
        "right_gripper_idler_link",
        "right_gripper_camera_mount_link",
    }
    LEFT_ARM_BODIES = {name.replace("right_", "left_", 1) for name in RIGHT_ARM_BODIES}
    # Mirror across Y=0 in raw MuJoCo coordinates (confirmed: shoulder_pitch sits at
    # y=+0.125 left / y=-0.125 right). A pure reflection has determinant -1 and inverts
    # face winding/normals, so faces are reversed to compensate.
    MIRROR_Y = np.diag([1.0, -1.0, 1.0, 1.0])

    world_parts: list[trimesh.Trimesh] = []
    for gid in visual_gids:
        body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, model.geom_bodyid[gid]) or ""
        if body_name in RIGHT_ARM_BODIES:
            continue
        m = geom_local_mesh(model, gid)
        if m is None:
            continue
        pos = data.geom_xpos[gid]
        rot = data.geom_xmat[gid].reshape(3, 3)
        world_mat = np.eye(4)
        world_mat[:3, :3] = rot
        world_mat[:3, 3] = pos
        m.apply_transform(world_mat)
        world_parts.append(m)

        if body_name in LEFT_ARM_BODIES:
            mirrored = m.copy()
            mirrored.apply_transform(MIRROR_Y)
            mirrored.faces = mirrored.faces[:, ::-1]
            world_parts.append(mirrored)

    combined = trimesh.util.concatenate(world_parts)
    combined.remove_unreferenced_vertices()
    combined.apply_transform(ZUP_TO_YUP)
    FLAT_GLB_OUT.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(FLAT_GLB_OUT))
    print(
        f"Wrote {FLAT_GLB_OUT} ({FLAT_GLB_OUT.stat().st_size / 1024:.1f} KB, {len(combined.vertices)} verts, {len(combined.faces)} tris)"
    )

    # ---- Decimated Resonite mesh-JSON (from the same flattened, correct geometry) ----
    target_tris = 8000
    decimated = combined.copy()
    if len(decimated.faces) > target_tris:
        decimated = decimated.simplify_quadric_decimation(face_count=target_tris)
    print(f"Decimated to {len(decimated.faces)} tris for the Resonite mesh-JSON payload")

    vertices_json = [{"position": {"x": float(v[0]), "y": float(v[1]), "z": float(v[2])}} for v in decimated.vertices]
    triangles_json = [
        {"vertex0Index": int(f[0]), "vertex1Index": int(f[1]), "vertex2Index": int(f[2])} for f in decimated.faces
    ]
    mesh_json = {"vertices": vertices_json, "submeshes": [{"$type": "triangles", "triangles": triangles_json}]}
    MESHJSON_OUT.write_text(json.dumps(mesh_json), encoding="utf-8")
    print(f"Wrote {MESHJSON_OUT} ({MESHJSON_OUT.stat().st_size / 1024:.1f} KB)")

    # ---- Per-body rig export (webapp 3D viewer, animatable) ----
    body_parts: dict[int, list[trimesh.Trimesh]] = {}
    for gid in visual_gids:
        m = geom_local_mesh(model, gid)
        if m is None:
            continue
        m.apply_transform(geom_local_matrix(model, gid))
        body_parts.setdefault(model.geom_bodyid[gid], []).append(m)

    scene = trimesh.Scene()
    world_parts_local = body_parts.get(0)
    if world_parts_local:
        # A handful of visual geoms (root sensor/shell parts) end up attached directly to the
        # world body - MuJoCo welds a fixed-jointed root URDF link straight into its parent
        # when it has no joint of its own. Attach them to the scene's actual root frame
        # ("world", trimesh's default base_frame) instead of silently dropping them.
        scene.add_geometry(trimesh.util.concatenate(world_parts_local), node_name="world")

    for body_id in range(1, model.nbody):  # body 0 is the world
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id) or f"body_{body_id}"
        parent_id = int(model.body_parentid[body_id])
        parent_name = (
            "world"
            if parent_id == 0
            else (mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, parent_id) or f"body_{parent_id}")
        )
        local_mat = body_local_matrix(model, body_id)

        parts = body_parts.get(body_id)
        geometry = trimesh.util.concatenate(parts) if parts else None
        if geometry is not None:
            scene.add_geometry(geometry, node_name=name, parent_node_name=parent_name, transform=local_mat)
        else:
            scene.graph.update(frame_to=name, frame_from=parent_name, matrix=local_mat)

    scene.apply_transform(ZUP_TO_YUP)
    RIG_GLB_OUT.parent.mkdir(parents=True, exist_ok=True)
    RIG_GLB_OUT.write_bytes(trimesh.exchange.gltf.export_glb(scene, include_normals=True))
    body_count = model.nbody - 1
    mesh_body_count = len(body_parts)
    print(
        f"Wrote {RIG_GLB_OUT} ({RIG_GLB_OUT.stat().st_size / 1024:.1f} KB, {body_count} nodes, {mesh_body_count} with geometry)"
    )


if __name__ == "__main__":
    main()
