import * as THREE from "three";
// @ts-expect-error - three examples have no bundled types entry
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
// @ts-expect-error - three examples have no bundled types entry
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

// One node per MuJoCo body in the rigged GLB (see scripts/export_posed_mesh.py). Axes and
// limits are read directly from the vendored URDF's <joint><axis>/<limit> - not guessed - so
// rotating a node about its own local axis is exactly the joint it represents.
interface WaveJoint {
  nodeName: string;
  axis: [number, number, number];
  /** radians, given elapsed seconds since the animation started */
  angle: (t: number) => number;
}

const RAISE_S = 0.7; // ramp-up duration for getting the arm into "waving" position

function smooth01(t: number, duration: number): number {
  const x = Math.min(Math.max(t / duration, 0), 1);
  return x * x * (3 - 2 * x);
}

// A recognizable "wave hello" on the left arm: raise it out to the side and up, bend the
// elbow, then wag the wrist. Left arm chosen arbitrarily; joints/axes/limits from the URDF's
// left_shoulder_pitch_joint / left_shoulder_roll_joint / left_elbow_pitch_joint /
// left_wrist_roll_joint.
const WAVE_JOINTS: WaveJoint[] = [
  {
    nodeName: "left_shoulder_pitch_link",
    axis: [0, 1, 0],
    angle: (t) => -1.3 * smooth01(t, RAISE_S),
  },
  {
    nodeName: "left_shoulder_roll_link",
    axis: [1, 0, 0],
    angle: (t) => 0.5 * smooth01(t, RAISE_S),
  },
  {
    nodeName: "left_elbow_pitch_link",
    axis: [0, 1, 0],
    angle: (t) => -1.1 * smooth01(t, RAISE_S),
  },
  {
    nodeName: "left_wrist_roll_link",
    axis: [-1, 0, 0],
    angle: (t) =>
      t < RAISE_S ? 0 : 0.7 * Math.sin((t - RAISE_S) * 2 * Math.PI * 1.1),
  },
];

export class BotViewer {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  renderer: THREE.WebGLRenderer;
  container: HTMLElement;
  model: THREE.Object3D | null = null;
  animFrame = 0;
  private resizeObserver: ResizeObserver;
  private homeTarget: THREE.Vector3 | null = null;
  private homeDistance: number | null = null;
  private waveNodes: {
    joint: WaveJoint;
    node: THREE.Object3D;
    restQuat: THREE.Quaternion;
    axis: THREE.Vector3;
  }[] = [];
  private waveStart = 0;
  private waveOn = false;
  private clock = new THREE.Clock();
  private spot: THREE.SpotLight;
  private spotHomePos = new THREE.Vector3(2, 2.5, 2);
  private spotOrbitRadius = 2;
  private spotOrbitHeight = 2.5;
  private spotOrbitOn = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0a1a);

    const w = container.clientWidth || 1;
    const h = container.clientHeight || 1;
    this.camera = new THREE.PerspectiveCamera(50, w / h, 0.01, 100);
    this.camera.position.set(1.4, 1.1, 1.6);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.target.set(0, 0.3, 0);
    this.controls.minDistance = 0.3;
    this.controls.maxDistance = 8;

    // Soft background ambient: a hemisphere light (sky/ground blend) reads more natural
    // than flat ambient alone, plus a little flat ambient so nothing goes fully black.
    const hemi = new THREE.HemisphereLight(0x9fb4d8, 0x2a2a35, 2.4);
    this.scene.add(hemi);
    const ambient = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(ambient);

    const dir = new THREE.DirectionalLight(0xffffff, 1.3);
    dir.position.set(2, 4, 3);
    dir.castShadow = true;
    this.scene.add(dir);
    const fill = new THREE.DirectionalLight(0x8899ff, 0.5);
    fill.position.set(-3, 1, -2);
    this.scene.add(fill);

    // Spotlight - the highlight that puts the bot "on a pedestal". Position/target/radius
    // get set relative to the model's actual bounding box once it loads (frameModel);
    // these are just sane pre-load defaults. decay=1 (not the physically-correct 2) so
    // intensity stays predictable to tune at this scene's small (~1m) scale.
    this.spot = new THREE.SpotLight(0xffffff, 45, 0, Math.PI / 7, 0.35, 1);
    this.spot.position.copy(this.spotHomePos);
    this.spot.castShadow = true;
    this.spot.shadow.mapSize.set(1024, 1024);
    this.spot.shadow.bias = -0.001;
    this.spot.target.name = "bot-spot-target";
    this.scene.add(this.spot);
    this.scene.add(this.spot.target);

    const grid = new THREE.GridHelper(3, 30, 0x334155, 0x1e293b);
    grid.name = "bot-grid";
    this.scene.add(grid);
    const axes = new THREE.AxesHelper(0.3);
    this.scene.add(axes);

    this.resizeObserver = new ResizeObserver(() => this.onResize());
    this.resizeObserver.observe(container);
  }

  async loadModel(url: string): Promise<{
    vertexCount: number;
    triangleCount: number;
    jointsFound: number;
  }> {
    if (this.model) {
      this.scene.remove(this.model);
      this.model = null;
    }
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(url);
    const model = gltf.scene as THREE.Object3D;

    let vertexCount = 0;
    let triangleCount = 0;
    model.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (mesh.isMesh && mesh.geometry) {
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        const geom = mesh.geometry;
        const posAttr = geom.getAttribute("position");
        if (posAttr) vertexCount += posAttr.count;
        triangleCount += geom.index
          ? geom.index.count / 3
          : posAttr
            ? posAttr.count / 3
            : 0;
        if (
          !mesh.material ||
          (Array.isArray(mesh.material) && mesh.material.length === 0)
        ) {
          mesh.material = new THREE.MeshStandardMaterial({
            color: 0xe2e8f0,
            roughness: 0.6,
            metalness: 0.15,
          });
        }
      }
    });

    this.scene.add(model);
    this.model = model;
    this.frameModel(model);

    this.waveNodes = [];
    for (const joint of WAVE_JOINTS) {
      const node = model.getObjectByName(joint.nodeName);
      if (!node) continue;
      this.waveNodes.push({
        joint,
        node,
        restQuat: node.quaternion.clone(),
        axis: new THREE.Vector3(...joint.axis).normalize(),
      });
    }

    return {
      vertexCount,
      triangleCount: Math.round(triangleCount),
      jointsFound: this.waveNodes.length,
    };
  }

  hasWaveJoints(): boolean {
    return this.waveNodes.length > 0;
  }

  setDemoAnimation(on: boolean) {
    this.waveOn = on;
    if (on) {
      this.waveStart = this.clock.getElapsedTime();
    } else {
      for (const { node, restQuat } of this.waveNodes)
        node.quaternion.copy(restQuat);
    }
  }

  private applyWave() {
    if (!this.waveOn) return;
    const t = this.clock.getElapsedTime() - this.waveStart;
    const q = new THREE.Quaternion();
    for (const { node, restQuat, axis, joint } of this.waveNodes) {
      q.setFromAxisAngle(axis, joint.angle(t));
      node.quaternion.copy(restQuat).multiply(q);
    }
  }

  setLightOrbit(on: boolean) {
    this.spotOrbitOn = on;
    if (!on) this.spot.position.copy(this.spotHomePos);
  }

  private applyLightOrbit() {
    if (!this.spotOrbitOn) return;
    const angle = this.clock.getElapsedTime() * 0.6; // rad/s - slow circle
    const cx =
      (this.homeTarget?.x ?? 0) + Math.cos(angle) * this.spotOrbitRadius;
    const cz =
      (this.homeTarget?.z ?? 0) + Math.sin(angle) * this.spotOrbitRadius;
    this.spot.position.set(cx, this.spotOrbitHeight, cz);
  }

  private frameModel(model: THREE.Object3D) {
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const radius = Math.max(size.x, size.y, size.z, 0.05) * 0.5;

    this.homeTarget = center.clone();
    this.homeDistance = radius * 2.6;

    this.spotOrbitRadius = radius * 2.4;
    this.spotOrbitHeight = center.y + radius * 2.2;
    this.spotHomePos = new THREE.Vector3(
      center.x + this.spotOrbitRadius * 0.7,
      this.spotOrbitHeight,
      center.z + this.spotOrbitRadius * 0.7,
    );
    this.spot.target.position.copy(center);
    this.spot.distance = radius * 10;
    this.spot.shadow.camera.near = Math.max(radius * 0.05, 0.01);
    this.spot.shadow.camera.far = radius * 12;
    if (!this.spotOrbitOn) this.spot.position.copy(this.spotHomePos);

    const grid = this.scene.getObjectByName("bot-grid") as
      | THREE.GridHelper
      | undefined;
    if (grid) {
      const gridSize = Math.max(radius * 4, 0.5);
      grid.scale.setScalar(gridSize / 3);
      grid.position.y = box.min.y;
    }

    this.resetView();
  }

  resetView() {
    const target = this.homeTarget ?? new THREE.Vector3(0, 0, 0);
    const distance = this.homeDistance ?? 2;
    this.camera.position.set(
      target.x + distance * 0.8,
      target.y + distance * 0.6,
      target.z + distance * 0.8,
    );
    this.controls.target.copy(target);
    this.controls.minDistance = distance * 0.1;
    this.controls.maxDistance = distance * 8;
    this.camera.near = Math.max(distance / 200, 0.001);
    this.camera.far = distance * 100;
    this.camera.updateProjectionMatrix();
    this.controls.update();
  }

  setWireframe(on: boolean) {
    this.model?.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (mesh.isMesh && mesh.material) {
        const mats = Array.isArray(mesh.material)
          ? mesh.material
          : [mesh.material];
        for (const m of mats) (m as THREE.MeshStandardMaterial).wireframe = on;
      }
    });
  }

  private onResize() {
    const w = this.container.clientWidth || 1;
    const h = this.container.clientHeight || 1;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  startLoop() {
    const tick = () => {
      this.applyWave();
      this.applyLightOrbit();
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
      this.animFrame = requestAnimationFrame(tick);
    };
    tick();
  }

  destroy() {
    cancelAnimationFrame(this.animFrame);
    this.resizeObserver.disconnect();
    this.controls.dispose();
    this.renderer.dispose();
    if (this.renderer.domElement.parentElement === this.container) {
      this.container.removeChild(this.renderer.domElement);
    }
  }
}
