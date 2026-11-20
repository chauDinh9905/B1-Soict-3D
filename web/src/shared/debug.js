import GUI from 'lil-gui';

/** Bảng chỉnh thông số khi mở URL có ?debug */
export function setupDebug(ctx) {
  const { world, bus } = ctx;
  window.b1 = ctx;   // gõ b1.engine.camera.position, b1.world.buildings... trong console
  const gui = new GUI({ title: 'Debug' });
  gui.add(world.lights.sun, 'intensity', 0, 6).name('Nắng');
  gui.add(world.lights.hemi, 'intensity', 0, 3).name('Trời');
  gui.add({ walk: () => bus.emit('nav:mode', 'walk') }, 'walk').name('Thử chế độ đi bộ');
  gui.add({ orbit: () => bus.emit('nav:mode', 'orbit') }, 'orbit').name('Về chế độ xoay');
  return gui;
}
