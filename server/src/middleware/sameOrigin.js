import { config } from '../config.js';

// Chống CSRF lớp thứ hai (lớp thứ nhất là cookie SameSite=Lax):
//  - request ghi dữ liệu phải có header Origin nằm trong APP_ORIGINS (hỗ trợ dấu * cho link Preview của Vercel)
//  - có body thì body phải là JSON
const SAFE = new Set(['GET', 'HEAD', 'OPTIONS']);
const toRegex = (pattern) =>
  new RegExp(`^${pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '[a-z0-9-]+')}$`, 'i');
const allowed = config.APP_ORIGINS.map(toRegex);

export function sameOrigin(req, res, next) {
  if (SAFE.has(req.method)) return next();
  const origin = req.get('origin');
  if (!origin || !allowed.some((re) => re.test(origin))) {
    return res.status(403).json({ error: 'Nguồn yêu cầu không hợp lệ', code: 'BAD_ORIGIN' });
  }
  const hasBody = Number(req.get('content-length') ?? 0) > 0 || req.get('transfer-encoding');
  if (hasBody && !req.is('application/json')) {
    return res.status(415).json({ error: 'Chỉ nhận dữ liệu JSON', code: 'UNSUPPORTED_MEDIA_TYPE' });
  }
  next();
}
