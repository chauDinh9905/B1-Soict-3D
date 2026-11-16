import { Router } from 'express';
import { query } from '../../infra/db.js';

/** GET /api/campus -> { name, buildings: ['b1', ...] } (cùng hình dạng web/public/data/campus.json) */
export function campusRoutes() {
  const r = Router();
  r.get('/', async (_req, res) => {
    const { rows } = await query('SELECT id FROM buildings WHERE enabled ORDER BY sort_order');
    res.json({ name: 'Đại học Bách khoa Hà Nội', buildings: rows.map((b) => b.id) });
  });
  return r;
}
