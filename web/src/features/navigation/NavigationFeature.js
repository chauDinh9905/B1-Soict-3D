import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { WalkMode } from './WalkMode.js';

const FLY_SECONDS = 1.1;
const _dir = new THREE.Vector3();
const _euler = new THREE.Euler(0, 0, 0, 'YXZ');
const ease = (t) => t * t * (3 - 2 * t);

/**
 * Điều hướng: 2 chế độ.
 *  - orbit: xoay quanh, nhìn tổng thể
 *  - walk : đi bộ góc nhìn người, WASD + chuột (xem WalkMode.js)
 * Sự kiện nghe: 'nav:mode' ('orbit'|'walk'), 'nav:noclip' (bool),
 *               'camera:flyTo' {position, target} – bay mượt (orbit) hoặc dịch chuyển (walk).
 */
export class NavigationFeature {
  init(ctx) {
    const { engine, bus, config } = ctx;
    this.engine = engine;
    this.bus = bus;
    this.orbit = new OrbitControls(engine.camera, engine.renderer.domElement);
    this.orbit.target.set(...config.CAMERA.target);
    this.orbit.enableDamping = true;
    this.orbit.maxPolarAngle = Math.PI * 0.49; // không cho chui xuống dưới đất
    this.orbit.minDistance = 0.5;              // cho phép đứng sát khi xem trong phòng
    this.orbit.maxDistance = 400;

    this.walk = new WalkMode(ctx);
    this.mode = 'orbit';
    this.fly = null;

    this.off = [
      bus.on('nav:mode', (m) => this.setMode(m)),
      bus.on('nav:noclip', (on) => { this.walk.noclip = !!on; }),
      bus.on('camera:flyTo', ({ position, target }) => this.flyTo(position, target)),
    ];
  }

  setMode(m) {
    if (m === this.mode) return;
    const cam = this.engine.camera;
    this.fly = null;
    this.mode = m;
    if (m === 'walk') {
      this.orbit.enabled = false;
      this.walk.enable();
    } else {
      this.walk.disable();
      // Đặt tâm xoay ngay trước mặt để chuyển chế độ không bị giật khung hình
      cam.getWorldDirection(_dir);
      this.orbit.target.copy(cam.position).addScaledVector(_dir, 8);
      this.orbit.enabled = true;
      this.orbit.update();
    }
    this.bus.emit('nav:modeChanged', m);
  }

  flyTo(position, target) {
    const cam = this.engine.camera;
    if (this.mode === 'walk') {
      // Đi bộ: dịch chuyển tức thì, đứng trên sàn tại đó, nhìn về target
      _dir.subVectors(target, position);
      _euler.set(0, Math.atan2(-_dir.x, -_dir.z), 0, 'YXZ');
      const horiz = Math.hypot(_dir.x, _dir.z);
      _euler.x = THREE.MathUtils.clamp(Math.atan2(_dir.y, horiz), -1.2, 1.2);
      this.walk.placeAt(position.x, position.z, _euler.y, _euler.x, position.y);
      return;
    }
    this.fly = {
      t: 0,
      fromPos: cam.position.clone(),
      toPos: position.clone(),
      fromTarget: this.orbit.target.clone(),
      toTarget: target.clone(),
    };
  }

  update(dt) {
    if (this.mode === 'walk') { this.walk.update(dt); return; }
    if (this.fly) {
      const f = this.fly;
      f.t = Math.min(1, f.t + dt / FLY_SECONDS);
      const k = ease(f.t);
      this.engine.camera.position.lerpVectors(f.fromPos, f.toPos, k);
      this.orbit.target.lerpVectors(f.fromTarget, f.toTarget, k);
      if (f.t >= 1) this.fly = null;
    }
    this.orbit.update();
  }

  dispose() { this.off.forEach((f) => f()); this.orbit.dispose(); this.walk.dispose(); }
}
