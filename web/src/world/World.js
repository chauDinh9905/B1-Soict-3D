import { createLighting } from './Lighting.js';
import { createGround } from './Ground.js';
import { Building } from './Building.js';

/** Thế giới = ánh sáng + mặt đất + danh sách tòa nhà lấy từ API (hoặc JSON tĩnh dự phòng). */
export class World {
  constructor(scene, assets, api, bus, renderer) {
    this.scene = scene;
    this.assets = assets;
    this.api = api;
    this.bus = bus;
    this.buildings = new Map();
    this.lights = createLighting(scene, renderer);
    this.ground = createGround(scene);
  }

  async load() {
    const campus = await this.api.getCampus();
    // Giai đoạn 1 chỉ có b1. Khi nhiều nhà: chỉ nạp nhà gần camera (lazy load).
    await Promise.all(campus.buildings.map((id) => this.addBuilding(id)));
  }

  async addBuilding(id) {
    const data = await this.api.getBuilding(id);
    const b = await new Building(data).load(this.assets);
    this.scene.add(b.root);
    this.buildings.set(id, b);
    this.bus.emit('building:loaded', b);
    // Phòng dựng riêng (sảnh...): nạp ở nền, không bắt world:ready phải chờ
    for (const def of data.interiors ?? []) {
      b.loadInterior(this.assets, def)
        .then(() => this.bus.emit('interior:loaded', { building: b, id: def.id, def }))
        .catch((err) => console.warn(`[${id}] không nạp được phòng ${def.id}:`, err.message));
    }
    return b;
  }

  /** Tất cả mesh va chạm của mọi tòa nhà – cho WalkMode. */
  get colliders() {
    return [...this.buildings.values()].flatMap((b) => b.colliders);
  }
}
