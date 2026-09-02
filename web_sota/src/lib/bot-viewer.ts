import * as THREE from "three";
// @ts-expect-error - three examples have no bundled types entry
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
// @ts-expect-error - three examples have no bundled types entry
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

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

    const ambient = new THREE.AmbientLight(0x404060, 1.2);
    this.scene.add(ambient);
    const dir = new THREE.DirectionalLight(0xffffff, 2.2);
    dir.position.set(2, 4, 3);
    dir.castShadow = true;
    this.scene.add(dir);
    const fill = new THREE.DirectionalLight(0x8899ff, 0.6);
    fill.position.set(-3, 1, -2);
    this.scene.add(fill);

    const grid = new THREE.GridHelper(3, 30, 0x334155, 0x1e293b);
    grid.name = "bot-grid";
    this.scene.add(grid);
    const axes = new THREE.AxesHelper(0.3);
    this.scene.add(axes);

    this.resizeObserver = new ResizeObserver(() => this.onResize());
    this.resizeObserver.observe(container);
  }

  async loadModel(
    url: string,
  ): Promise<{ vertexCount: number; triangleCount: number }> {
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
    return { vertexCount, triangleCount: Math.round(triangleCount) };
  }

  private frameModel(model: THREE.Object3D) {
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const radius = Math.max(size.x, size.y, size.z, 0.05) * 0.5;

    this.homeTarget = center.clone();
    this.homeDistance = radius * 2.6;

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
      target.x + distance * 0.55,
      target.y + distance * 0.45,
      target.z + distance * 0.65,
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
