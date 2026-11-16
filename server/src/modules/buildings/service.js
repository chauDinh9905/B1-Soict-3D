import { query } from '../../infra/db.js';

/** Đổi dòng CSDL thành đúng hình dạng JSON frontend đang đọc (web/public/data/buildings/b1.json). */
export async function getBuilding(id) {
  const { rows: [b] } = await query('SELECT * FROM buildings WHERE id = $1', [id]);
  if (!b) return null;
  const { rows: pois } = await query('SELECT * FROM pois WHERE building_id = $1 ORDER BY id', [id]);
  return {
    id: b.id,
    name: b.name,
    model: b.model,
    origin: { lat: b.lat, lon: b.lon },
    rotationDeg: b.rotation_deg,
    placeholder: { size: b.placeholder },
    description: b.description,
    pois: pois.map((p) => ({ id: p.id, title: p.title, position: [p.x, p.y, p.z], text: p.text, image: p.image })),
    views: b.views ?? [],
  };
}
