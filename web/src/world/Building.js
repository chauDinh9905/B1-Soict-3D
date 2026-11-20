import * as THREE from 'three';
import { latLonToWorld } from './geo.js';

/** Một tòa nhà: đọc data JSON, nạp .glb, đặt đúng vị trí trên bản đồ khuôn viên. */
export class Building {
  constructor(data) {
    this.data = data;
    this.id = data.id;
    this.root = new THREE.Group();
    this.root.name = `Building_${data.id}`;
    this.colliders = [];   // mesh COL_* – dùng cho đi bộ
    this.cameras = {};     // Cam_* từ Blender – dùng cho tour
    this.poiAnchors = {};  // POI_* từ Blender
    this.interiors = {};   // id -> { def, root }: phòng dựng thành model riêng (data.interiors)
  }

  /**
   * Nạp một phòng (glb riêng). Phòng xuất từ Blender cùng hệ toạ độ với vỏ ngoài,
   * nên chỉ cần gắn vào this.root như glb tòa nhà.
   */
  async loadInterior(assets, def) {
    if (this.interiors[def.id]) return this.interiors[def.id];
    const gltf = await assets.loadGLTF(def.model);
    const root = gltf.scene;
    root.name = `Interior_${def.id}`;
    root.traverse((o) => {
      if (o.isMesh) { o.castShadow = false; o.receiveShadow = true; }
      if (o.name.startsWith('COL_')) { o.visible = false; this.colliders.push(o); }
      if (o.name.startsWith('POI_')) this.poiAnchors[o.name] = o;
    });
    gltf.cameras.forEach((c) => { this.cameras[c.name] = c; });
    this.root.add(root);
    this.interiors[def.id] = { def, root };
    return this.interiors[def.id];
  }

  async load(assets) {
    try {
      const gltf = await assets.loadGLTF(this.data.model);
      this.root.add(gltf.scene);
      gltf.scene.traverse((o) => {
        if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
        if (o.name.startsWith('COL_')) { o.visible = false; this.colliders.push(o); }
        if (o.name.startsWith('POI_')) this.poiAnchors[o.name] = o;
      });
      gltf.cameras.forEach((c) => { this.cameras[c.name] = c; });
    } catch (err) {
      console.warn(`[${this.id}] chưa có model, dùng khối tạm.`, err.message);
      const [w, h, d] = this.data.placeholder?.size ?? [20, 20, 20];
      const box = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color: 0xdddddd }));
      box.position.y = h / 2;
      box.castShadow = true;
      this.root.add(box);
      this.colliders.push(box);
    }
    const { lat, lon } = this.data.origin;
    this.root.position.copy(latLonToWorld(lat, lon));
    this.root.rotation.y = THREE.MathUtils.degToRad(this.data.rotationDeg ?? 0);
    return this;
  }
}
