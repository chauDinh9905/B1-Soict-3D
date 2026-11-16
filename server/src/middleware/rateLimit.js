import { rateLimit, ipKeyGenerator } from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';

// Bộ đếm nằm trên Redis → đúng cả khi có nhiều bản sao server.
// Mỗi bộ giới hạn cần MỘT store riêng (prefix riêng).
function limiter(redis, name, { windowMs, limit, key }) {
  return rateLimit({
    windowMs,
    limit,
    standardHeaders: 'draft-8',
    legacyHeaders: false,
    keyGenerator: key ?? ((req) => ipKeyGenerator(req.ip)),
    store: new RedisStore({ prefix: `rl:${name}:`, sendCommand: (...args) => redis.sendCommand(args) }),
    handler: (_req, res) => res.status(429).json({ error: 'Thử quá nhiều lần, vui lòng đợi rồi thử lại', code: 'RATE_LIMITED' }),
  });
}

const emailKey = (req) => `${ipKeyGenerator(req.ip)}:${String(req.body?.email ?? '').trim().toLowerCase()}`;
const MIN = 60 * 1000;

export function createLimiters(redis) {
  return {
    loginPerEmail: limiter(redis, 'login-email', { windowMs: 15 * MIN, limit: 5, key: emailKey }),
    loginPerIp: limiter(redis, 'login-ip', { windowMs: 15 * MIN, limit: 50 }),
    register: limiter(redis, 'register', { windowMs: 60 * MIN, limit: 5 }),
  };
}
