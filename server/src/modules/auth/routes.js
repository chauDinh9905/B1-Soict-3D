// TẦNG HTTP: đường dẫn, kiểm tra đầu vào, gọi service, trả JSON.
import { Router } from 'express';
import { requireAuth } from '../../middleware/requireAuth.js';
import { registerBody, loginBody } from './schemas.js';
import * as auth from './service.js';

export function authRoutes({ redis, limiters }) {
  const r = Router();

  r.post('/register', limiters.register, async (req, res) => {
    const body = registerBody.parse(req.body ?? {});
    const user = await auth.register(body);
    await auth.establishSession(req, redis, user);     // đăng ký xong là đăng nhập luôn (BACKEND_PLAN mục 8.2)
    res.status(201).json({ user: auth.toPublicUser(user) });
  });

  r.post('/login', limiters.loginPerIp, limiters.loginPerEmail, async (req, res) => {
    const body = loginBody.parse(req.body ?? {});
    const user = await auth.login({ ...body, ip: req.ip, userAgent: req.get('user-agent') });
    await auth.establishSession(req, redis, user);
    res.json({ user: auth.toPublicUser(user) });
  });

  r.post('/logout', async (req, res) => {
    await auth.endSession(req, res, redis);
    res.status(204).end();
  });

  r.get('/me', requireAuth, (req, res) => {
    res.json({ user: auth.toPublicUser(req.user) });
  });

  // TODO giai đoạn B (tuần 9–10): verify-email, password/forgot, password/reset, sessions – xem BACKEND_PLAN mục 8.1. Google để sau giai đoạn này.
  return r;
}
