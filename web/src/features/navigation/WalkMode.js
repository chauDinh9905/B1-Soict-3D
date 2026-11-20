import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { damp } from '../../shared/math.js';

// Đồ nội thất / chi tiết nhỏ: không chặn đường, không đứng lên được (tránh kẹt giữa dãy ghế).
const SKIP_NAME = /Chair|Desk|Plant|Bench|Downlight|Joint|Pattern|Sign|ACUnit|Mast|WaterTank/i;
const RADIUS = 0.35;     // bán kính "thân người"
const STEP_UP = 0.5;     // bước lên được bậc cao tối đa
const LOOK_KEYS = 1.8;   // rad/s khi xoay bằng phím mũi tên

const _dir = new THREE.Vector3();
const _fwd = new THREE.Vector3();
const _right = new THREE.Vector3();
const _move = new THREE.Vector3();
const _origin = new THREE.Vector3();
const _down = new THREE.Vector3(0, -1, 0);
const _euler = new THREE.Euler(0, 0, 0, 'YXZ');

/**
 * Đi bộ góc nhìn thứ nhất.
 *  - Click vào màn hình để khóa chuột, rê chuột để nhìn; Esc để thả chuột.
 *  - W/A/S/D (hoặc di chuyển), Shift chạy, mũi tên ←/→/↑/↓ để xoay khi chưa khóa chuột.
 *  - Va chạm: tia ngang vào mesh tòa nhà; đứng trên sàn bằng tia hướng xuống (lên được bậc ≤ 0.5 m).
 *  - Vật liệu trong suốt (kính) không chặn, để không bị kẹt ở cửa kính. Bật "xuyên tường" để bỏ va chạm.
 */
export class WalkMode {
  constructor(ctx) {
    this.ctx = ctx;
    this.enabled = false;
    this.noclip = false;
    this.keys = new Set();
    this.raycaster = new THREE.Raycaster();
    this.raycaster.firstHitOnly = true;
    this.solids = [];
    this.floorY = 0;   // độ cao sàn đang đứng (mượt)
    this.feetY = 0;
    this.controls = new PointerLockControls(ctx.engine.camera, ctx.engine.renderer.domElement);
    this.canvas = ctx.engine.renderer.domElement;
    this._onKey = (e) => this.onKey(e, true);
    this._onKeyUp = (e) => this.onKey(e, false);
    this._onClick = () => { if (this.enabled && !this.controls.isLocked) this.controls.lock(); };
    this._onBlur = () => this.keys.clear();
    const reset = () => { this.solids = null; };                       // dựng lại khi có model mới
    this.offs = [ctx.bus.on('building:loaded', reset), ctx.bus.on('interior:loaded', reset)];
  }

  /** Object (hoặc node cha, vì mesh nhiều vật liệu thành Group) có cờ noCollide từ Blender (glTF extras). */
  static passable(o) {
    for (let p = o; p; p = p.parent) {
      if (p.userData?.noCollide) return true;
      if (p.name.startsWith('Building_')) break;
    }
    return false;
  }

  /**
   * Mesh dùng để va chạm / đứng lên. Ưu tiên mesh COL_* nếu Blender có xuất; không thì lấy mọi mesh
   * tòa nhà trừ đồ nội thất và vật liệu trong suốt.
   */
  collectSolids() {
    const col = [];
    const list = [];
    for (const b of this.ctx.world.buildings.values()) {
      b.root.updateMatrixWorld(true);
      b.root.traverse((o) => {
        if (!o.isMesh) return;
        if (o.name.startsWith('COL_')) { col.push(o); return; }
        if (SKIP_NAME.test(o.name) || SKIP_NAME.test(o.parent?.name ?? '') || WalkMode.passable(o)) return;
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        if (mats.every((m) => m.transparent || m.opacity < 1 || m.transmission > 0)) return;
        list.push(o);
      });
    }
    const solids = col.length ? col : list;
    this.materials = [...new Set(solids.flatMap((o) => (Array.isArray(o.material) ? o.material : [o.material])))];
    return solids;
  }

  get solidList() {
    if (!this.solids) this.solids = this.collectSolids();
    return this.solids;
  }

  enable() {
    this.enabled = true;
    const cam = this.ctx.engine.camera;
    // Giữ hướng nhìn đang có, bỏ nghiêng (roll)
    _euler.setFromQuaternion(cam.quaternion);
    _euler.z = 0;
    cam.quaternion.setFromEuler(_euler);
    this.placeAt(cam.position.x, cam.position.z);
    window.addEventListener('keydown', this._onKey);
    window.addEventListener('keyup', this._onKeyUp);
    window.addEventListener('blur', this._onBlur);
    this.canvas.addEventListener('click', this._onClick);
    this.ctx.bus.emit('walk:state', { active: true });
  }

  disable() {
    if (!this.enabled) return;
    this.enabled = false;
    this.keys.clear();
    if (this.controls.isLocked) this.controls.unlock();
    window.removeEventListener('keydown', this._onKey);
    window.removeEventListener('keyup', this._onKeyUp);
    window.removeEventListener('blur', this._onBlur);
    this.canvas.removeEventListener('click', this._onClick);
    this.ctx.bus.emit('walk:state', { active: false });
  }

  /**
   * Đặt người đứng tại (x,z) trên sàn gần nhất bên dưới độ cao fromY (mặc định: tầm mắt hiện tại).
   * Giới hạn 3.5 m để không đáp lên mái/trần khi đang ở góc nhìn từ trên cao.
   */
  placeAt(x, z, yaw, pitch, fromY) {
    const cam = this.ctx.engine.camera;
    if (yaw !== undefined) {
      _euler.set(pitch ?? 0, yaw, 0, 'YXZ');
      cam.quaternion.setFromEuler(_euler);
    }
    const startY = Math.min((fromY ?? cam.position.y) + 0.3, 3.5);
    const y = this.sampleFloor(x, z, startY);
    this.floorY = y;
    this.feetY = y;
    cam.position.set(x, y + this.ctx.config.WALK.eyeHeight, z);
  }

  /** Độ cao sàn tại (x,z), tìm từ độ cao fromY đi xuống; không thấy thì 0 (mặt đất). */
  sampleFloor(x, z, fromY) {
    const solids = this.solidList;
    if (!solids.length) return 0;
    _origin.set(x, fromY, z);
    this.raycaster.set(_origin, _down);
    this.raycaster.far = fromY + 50;
    const hit = this.raycaster.intersectObjects(solids, false)[0];
    return Math.max(0, hit ? hit.point.y : 0);
  }

  onKey(e, down) {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
    const k = e.code;
    if (!/^(KeyW|KeyA|KeyS|KeyD|ShiftLeft|ShiftRight|Arrow(Up|Down|Left|Right))$/.test(k)) return;
    if (k.startsWith('Arrow')) e.preventDefault();
    if (down) this.keys.add(k); else this.keys.delete(k);
  }

  /** Có vật cản theo hướng dir (đã chuẩn hóa) trong khoảng dist ở hai độ cao (đầu gối, ngực)? */
  blocked(pos, dir, dist) {
    const solids = this.solidList;
    if (this.noclip || !solids.length) return false;
    this.raycaster.far = dist + RADIUS;
    // Tường một lớp chỉ có mặt trước: tạm cho raycast tính cả mặt sau để không đi xuyên từ phía trong
    const sides = this.materials.map((m) => m.side);
    this.materials.forEach((m) => { m.side = THREE.DoubleSide; });
    let hit = false;
    for (const h of [0.35, 1.1]) {
      _origin.set(pos.x, this.feetY + h, pos.z);
      this.raycaster.set(_origin, dir);
      if (this.raycaster.intersectObjects(solids, false).length) { hit = true; break; }
    }
    this.materials.forEach((m, i) => { m.side = sides[i]; });
    return hit;
  }

  update(dt) {
    if (!this.enabled) return;
    const cam = this.ctx.engine.camera;
    const { speed, runSpeed, eyeHeight } = this.ctx.config.WALK;
    const k = this.keys;

    // Xoay bằng phím mũi tên (khi chưa khóa chuột, hoặc máy không hỗ trợ khóa chuột)
    const turn = (k.has('ArrowLeft') ? 1 : 0) - (k.has('ArrowRight') ? 1 : 0);
    const tilt = (k.has('ArrowUp') ? 1 : 0) - (k.has('ArrowDown') ? 1 : 0);
    if (turn || tilt) {
      _euler.setFromQuaternion(cam.quaternion);
      _euler.y += turn * LOOK_KEYS * dt;
      _euler.x = THREE.MathUtils.clamp(_euler.x + tilt * LOOK_KEYS * dt, -1.45, 1.45);
      cam.quaternion.setFromEuler(_euler);
    }

    // Hướng đi: theo hướng nhìn, chiếu xuống mặt phẳng ngang
    cam.getWorldDirection(_fwd);
    _fwd.y = 0;
    _fwd.normalize();
    _right.crossVectors(_fwd, cam.up).normalize();
    const f = (k.has('KeyW') ? 1 : 0) - (k.has('KeyS') ? 1 : 0);
    const r = (k.has('KeyD') ? 1 : 0) - (k.has('KeyA') ? 1 : 0);
    if (f || r) {
      _move.set(0, 0, 0).addScaledVector(_fwd, f).addScaledVector(_right, r).normalize();
      const v = k.has('ShiftLeft') || k.has('ShiftRight') ? runSpeed : speed;
      const step = v * dt;
      // Thử đi từng trục để trượt dọc theo tường thay vì dừng cứng
      for (const axis of ['x', 'z']) {
        const comp = _move[axis] * step;
        if (Math.abs(comp) < 1e-6) continue;
        _dir.set(0, 0, 0);
        _dir[axis] = Math.sign(comp);
        if (!this.blocked(cam.position, _dir, Math.abs(comp))) cam.position[axis] += comp;
      }
    }

    // Bám sàn: tìm sàn dưới chân (lên được bậc ≤ STEP_UP), hạ xuống mượt
    const target = this.sampleFloor(cam.position.x, cam.position.z, this.feetY + STEP_UP);
    this.floorY = damp(this.floorY, target, target > this.floorY ? 18 : 10, dt);
    this.feetY = this.floorY;
    cam.position.y = this.feetY + eyeHeight;
  }

  dispose() {
    this.offs.forEach((f) => f());
    this.disable();
    this.controls.dispose();
  }
}
