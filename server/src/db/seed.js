// Nạp nội dung (tòa nhà, POI) từ JSON vào Postgres. CHỈ đụng bảng nội dung, không bao giờ đụng users.
// Đường dẫn dữ liệu: biến CONTENT_DIR (mặc định ../web/public/data khi chạy trong thư mục server/).
import { readFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from '../config.js';
import { pool, tx } from '../infra/db.js';
import { migrate } from '../infra/migrate.js';

const DATA = resolve(config.CONTENT_DIR);
const read = async (p) => JSON.parse(await readFile(join(DATA, p), 'utf8'));

export async function seed() {
  const campus = await read('campus.json');
  const buildings = await Promise.all(campus.buildings.map((id) => read(`buildings/${id}.json`)));
  await tx(async (c) => {
    await c.query('DELETE FROM pois');
    await c.query('DELETE FROM buildings');
    for (const [i, b] of buildings.entries()) {
      await c.query(
        `INSERT INTO buildings (id, name, description, model, lat, lon, rotation_deg, placeholder, views, sort_order)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [b.id, b.name, b.description ?? null, b.model, b.origin.lat, b.origin.lon, b.rotationDeg ?? 0,
          JSON.stringify(b.placeholder?.size ?? null), JSON.stringify(b.views ?? []), i],
      );
      for (const p of b.pois ?? []) {
        await c.query(
          'INSERT INTO pois (id, building_id, title, text, image, x, y, z) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)',
          [p.id, b.id, p.title, p.text ?? null, p.image ?? null, ...p.position],
        );
      }
    }
  });
  return buildings.length;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  migrate()
    .then(seed)
    .then((n) => console.log(`[seed] đã nạp ${n} tòa nhà từ ${DATA}`))
    .catch((err) => { console.error('[seed]', err.message); process.exitCode = 1; })
    .finally(() => pool.end());
}
