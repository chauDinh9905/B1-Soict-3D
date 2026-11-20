import * as THREE from 'three';
import './viewer.css';

// Nhãn tiếng Việt cho camera Cam_* xuất từ Blender; tên lạ vẫn hiện, bằng tên gốc.
const LABELS = {
  Cam_Ref: 'Mặt trước (ảnh ref)',
  Cam_Aerial: 'Toàn cảnh từ trên cao',
  Cam_Lobby: 'Vành sảnh',
  Cam_Porch: 'Dưới mái đón xe',
  Cam_SanhEntry: 'Cửa vào sảnh',
  Cam_SanhHust: 'Nhìn vào lễ tân',
  Cam_SanhGlass: 'Mặt kính sảnh',
  Cam_SanhPortal: 'Cổng ra hành lang',
  Cam_SanhHall: 'Sảnh sau nhìn ra cửa',
  Cam_SanhLifts34: 'Thang máy 3–4, cầu thang',
  Cam_SanhLifts12: 'Thang máy 1–2',
  Cam_SanhCorrW: 'Hành lang tây cạnh thang 1–2',  Cam_SanhBack: 'Lối ra cửa sau',
  Cam_SanhPlan: 'Sảnh – nhìn từ trên',
  Cam_AudStage: 'Giảng đường – sân khấu',
  Cam_AudBoard: 'Giảng đường – bảng',
  Cam_AudRear: 'Giảng đường – cuối phòng',
  Cam_AudBalcony: 'Giảng đường – ban công',
  Cam_AudPlan: 'Giảng đường – nhìn từ trên',
};
const GROUPS = [
  { title: 'Bên ngoài', test: /^Cam_(Ref|Aerial|Lobby|Porch)$/ },
  { title: 'Sảnh B1', test: /^Cam_Sanh/ },
  { title: 'Giảng đường B1', test: /^Cam_Aud/ },
];

const _pos = new THREE.Vector3();
const _dir = new THREE.Vector3();
const _ray = new THREE.Raycaster();

/**
 * Bảng xem model: chuyển Xoay / Đi bộ, nhảy tới các camera dựng sẵn, bật xuyên tường.
 * Chỉ phát/nghe sự kiện: 'nav:mode', 'nav:noclip', 'nav:modeChanged', 'camera:flyTo'.
 */
export class ViewerFeature {
  init(ctx) {
    this.ctx = ctx;
    const { bus, uiRoot } = ctx;

    this.el = document.createElement('aside');
    this.el.className = 'viewer';
    this.el.innerHTML = `
      <div class="viewer__head">
        <strong>Xem model B1</strong>
        <button type="button" class="viewer__fold" aria-label="Thu gọn">–</button>
      </div>
      <div class="viewer__body">
        <div class="viewer__modes" role="group" aria-label="Chế độ">
          <button type="button" data-mode="orbit" class="is-on">Xoay quanh</button>
          <button type="button" data-mode="walk">Đi bộ</button>
        </div>
        <p class="viewer__hint"></p>
        <label class="viewer__noclip"><input type="checkbox" /> Xuyên tường (khi đi bộ bị kẹt)</label>
        <div class="viewer__rooms"></div>
        <div class="viewer__views"><em>Đang tải model…</em></div>
      </div>`;
    uiRoot.appendChild(this.el);

    this.hint = this.el.querySelector('.viewer__hint');
    this.views = this.el.querySelector('.viewer__views');
    this.rooms = this.el.querySelector('.viewer__rooms');
    this.roomBtns = {};
    this.setHint('orbit');

    this.el.querySelector('.viewer__fold').addEventListener('click', () => this.el.classList.toggle('is-folded'));
    this.el.querySelectorAll('[data-mode]').forEach((b) =>
      b.addEventListener('click', () => bus.emit('nav:mode', b.dataset.mode)));
    this.el.querySelector('input').addEventListener('change', (e) => bus.emit('nav:noclip', e.target.checked));

    this.off = [
      bus.on('nav:modeChanged', (m) => {
        this.el.querySelectorAll('[data-mode]').forEach((b) => b.classList.toggle('is-on', b.dataset.mode === m));
        this.setHint(m);
      }),
      bus.on('building:loaded', (b) => { this.buildRooms(b); this.buildViews(b); }),
      bus.on('interior:loaded', ({ building, id }) => {
        const btn = this.roomBtns[id];
        if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label; }
        this.buildViews(building);
      }),
    ];
  }

  /** Nút "Vào <phòng>" cho mỗi phòng dựng riêng; bật khi glb phòng nạp xong. */
  buildRooms(building) {
    for (const def of building.data.interiors ?? []) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'viewer__room';
      btn.dataset.label = `Vào ${def.name}`;
      btn.textContent = `${btn.dataset.label} (đang tải…)`;
      btn.disabled = !building.interiors[def.id];
      btn.addEventListener('click', () => {
        this.ctx.bus.emit('nav:mode', 'walk');
        this.goTo(building, def.entry);
      });
      this.roomBtns[def.id] = btn;
      this.rooms.appendChild(btn);
    }
  }

  setHint(mode) {
    this.hint.textContent = mode === 'walk'
      ? 'Click vào màn hình để khóa chuột, rê chuột để nhìn. W A S D đi, Shift chạy, ←↑→↓ xoay, Esc thả chuột.'
      : 'Kéo chuột trái xoay, chuột phải di chuyển, lăn chuột để zoom.';
  }

  buildViews(building) {
    const names = Object.keys(building.cameras);
    this.views.replaceChildren();
    if (!names.length) { this.views.textContent = 'Model không có camera Cam_*.'; return; }
    const rest = new Set(names);
    for (const g of GROUPS) {
      const list = names.filter((n) => g.test.test(n));
      list.forEach((n) => rest.delete(n));
      this.addGroup(g.title, list, building);
    }
    this.addGroup('Khác', [...rest], building);
  }

  addGroup(title, names, building) {
    if (!names.length) return;
    const h = document.createElement('h3');
    h.textContent = title;
    this.views.appendChild(h);
    for (const name of names) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = LABELS[name] ?? name;
      btn.addEventListener('click', () => this.goTo(building, name));
      this.views.appendChild(btn);
    }
  }

  /** Bay tới camera Blender; tâm xoay = điểm camera đang nhìn trúng trên model (không có thì 30 m phía trước). */
  goTo(building, name) {
    const cam = building.cameras[name];
    if (!cam) return;
    cam.updateWorldMatrix(true, false);
    cam.getWorldPosition(_pos);
    cam.getWorldDirection(_dir);
    _ray.set(_pos, _dir);
    const hit = _ray.intersectObject(building.root, true).find((h) => h.object.isMesh && h.object.visible);
    const dist = hit ? Math.max(2, hit.distance) : 30;
    const target = _pos.clone().addScaledVector(_dir, dist);
    this.ctx.bus.emit('camera:flyTo', { position: _pos.clone(), target });
  }

  dispose() { this.off.forEach((f) => f()); this.el.remove(); }
}
