import { ZodError } from 'zod';
import { AppError } from '../shared/errors.js';

/** Lỗi nào chưa bắt ở route thì về đây. Luôn trả { error, code } – định dạng frontend đang đọc. */
export function errorHandler(err, req, res, _next) {
  if (err instanceof AppError) return res.status(err.status).json({ error: err.message, code: err.code });
  if (err instanceof ZodError) {
    const first = err.issues[0];
    return res.status(400).json({
      error: first?.message ?? 'Dữ liệu không hợp lệ',
      code: 'VALIDATION',
      fields: err.issues.map((i) => ({ path: i.path.join('.'), message: i.message })),
    });
  }
  if (err?.type === 'entity.parse.failed') return res.status(400).json({ error: 'JSON không hợp lệ', code: 'BAD_JSON' });
  if (err?.type === 'entity.too.large') return res.status(413).json({ error: 'Dữ liệu quá lớn', code: 'TOO_LARGE' });
  if (err?.code === '23505') return res.status(409).json({ error: 'Dữ liệu bị trùng', code: 'CONFLICT' });
  (req.log ?? console).error({ err }, 'Lỗi chưa xử lý');
  res.status(500).json({ error: 'Lỗi máy chủ', code: 'INTERNAL' });
}
