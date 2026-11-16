import { Router } from 'express';
import { query } from '../../infra/db.js';
import { requireRole } from '../../middleware/requireRole.js';

export function statsRoutes() {
  const r = Router();
  // Cộng 1 nguyên tử: nhiều request cùng lúc vẫn đếm đúng.
  r.post('/visit', async (_req, res) => {
    await query(`INSERT INTO visits (day, count) VALUES (current_date, 1)
                 ON CONFLICT (day) DO UPDATE SET count = visits.count + 1`);
    res.status(204).end();
  });
  r.get('/', requireRole('admin'), async (_req, res) => {
    const { rows } = await query('SELECT day::text AS day, count FROM visits ORDER BY day DESC LIMIT 60');
    res.json(rows);
  });
  return r;
}
