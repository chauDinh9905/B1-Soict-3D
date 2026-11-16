import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { WalkMode } from './WalkMode.js';

/**
 * Điều hướng: 2 chế độ.
 *  - orbit: xoay quanh, nhìn tổng thể (đã chạy)
 *  - walk : đi bộ góc nhìn người, WASD + chuột (TODO trong WalkMode.js)
 * Nghe 'nav:mode' để đổi, 'camera:flyTo' để tới góc nhìn (TODO: chuyển cảnh mượt).
 */
export class NavigationFeature {
  init(ctx) {
    const { engine, bus, config } = ctx;

    this.orbit = new OrbitControls(engine.camera, engine.renderer.domElement);
    this.orbit.target.set(...config.CAMERA.target);
    this.orbit.enableDamping = true;
    this.orbit.minDistance = 5;
    this.orbit.maxDistance = 400;

    // Math.PI * 0.49 = không cho camera xuống dưới mặt đất.
    // Đặt Math.PI nếu muốn nhìn từ dưới lên như Blender (khi làm việc).
    this.orbit.maxPolarAngle = Math.PI * 0.49;

    // Nút chuột kiểu Blender: giữa = xoay, phải = kéo dời; chuột trái vẫn xoay cho người quen web.
    this.orbit.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.ROTATE,
      RIGHT: THREE.MOUSE.PAN,
    };
    this.orbit.screenSpacePanning = true; // kéo dời theo mặt phẳng màn hình, giống Blender

    this.walk = new WalkMode(ctx);
    this.mode = 'orbit';

    // Mọi bus.on đều cất hàm hủy vào this.off để dispose() dọn được
    this.off = [
      bus.on('nav:mode', (m) => this.setMode(m)),
      bus.on('camera:flyTo', ({ position, target }) => {
        // TODO: tween bằng gsap hoặc dùng damp() trong shared/math.js
        engine.camera.position.copy(position);
        this.orbit.target.copy(target);
      }),
      // Xoay quanh tâm thật của tòa nhà thay vì điểm cố định
      bus.on('building:loaded', (b) => {
        const center = new THREE.Box3().setFromObject(b.root).getCenter(new THREE.Vector3());
        this.orbit.target.copy(center);
      }),
    ];
  }

  setMode(m) {
    this.mode = m;
    this.orbit.enabled = m === 'orbit';
    if (m === 'walk') this.walk.enable();
    else this.walk.disable();
  }

  update(dt) {
    if (this.mode === 'orbit') this.orbit.update();
    else this.walk.update(dt);
  }

  dispose() {
    this.off.forEach((f) => f());
    this.orbit.dispose();
    this.walk.disable();
  }
}