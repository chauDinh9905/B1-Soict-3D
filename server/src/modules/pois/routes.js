import { Router } from 'express';
import { requireRole } from '../../middleware/requireRole.js';

/**
 * TODO: thêm / sửa / xóa điểm thông tin – chỉ quản trị viên.
 *   POST   /api/pois        body { id, buildingId, title, text, image, position:[x,y,z] }
 *   PUT    /api/pois/:id    body như trên (trừ id)
 *   DELETE /api/pois/:id
 * Theo khuôn 3 tầng của modules/auth: routes.js + service.js + repository.js + schemas.js (zod), kèm test.
 */
export function poiRoutes() {
  const r = Router();
  r.use(requireRole('admin'));
  r.use((_req, res) => res.status(501).json({ error: 'Chưa làm', code: 'NOT_IMPLEMENTED' }));
  return r;
}
