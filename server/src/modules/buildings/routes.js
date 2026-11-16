import { Router } from 'express';
import { getBuilding } from './service.js';
import { httpError } from '../../shared/errors.js';

export function buildingRoutes() {
  const r = Router();
  r.get('/:id', async (req, res) => {
    const b = await getBuilding(req.params.id);
    if (!b) throw httpError(404, 'Không có tòa nhà này');
    res.json(b);
  });
  // TODO (Sprint 4): PUT /:id (requireRole('admin')) – sửa tên, mô tả
  return r;
}
