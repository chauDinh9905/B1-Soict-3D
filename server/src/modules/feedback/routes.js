import { Router } from 'express';
import { z } from 'zod';
import { query } from '../../infra/db.js';
import { requireRole } from '../../middleware/requireRole.js';
import { optionalText } from '../../shared/schemas.js';

const feedbackBody = z.object({
  message: z.string().trim().min(1, 'Thiếu nội dung').max(1000, 'Nội dung dài quá 1000 ký tự'),
  name: optionalText(100),
  poiId: optionalText(100),
});

export function feedbackRoutes() {
  const r = Router();
  // Ai cũng gửi được; đã đăng nhập thì gắn với tài khoản.
  r.post('/', async (req, res) => {
    const { message, name, poiId } = feedbackBody.parse(req.body ?? {});
    const { rows: [row] } = await query(
      'INSERT INTO feedback (name, message, poi_id, user_id) VALUES ($1, $2, $3, $4) RETURNING id',
      [name, message, poiId, req.user?.id ?? null],
    );
    res.status(201).json({ id: Number(row.id) });
  });
  r.get('/', requireRole('admin'), async (_req, res) => {
    const { rows } = await query(
      `SELECT id::int AS id, name, message, poi_id AS "poiId", user_id AS "userId", created_at AS "createdAt"
       FROM feedback ORDER BY id DESC LIMIT 200`,
    );
    res.json(rows);
  });
  return r;
}
