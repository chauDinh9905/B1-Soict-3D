import session from 'express-session';
import { RedisStore } from 'connect-redis';
import { config } from '../config.js';

const SEVEN_DAYS = 7 * 24 * 60 * 60 * 1000;
export const ABSOLUTE_MAX_MS = 30 * 24 * 60 * 60 * 1000;
export const COOKIE_NAME = 'sid';

export const cookieOptions = {
  httpOnly: true,                // JavaScript trên trang không đọc được
  secure: config.isProd,         // chỉ gửi qua HTTPS ở production
  sameSite: 'lax',               // không gửi kèm POST từ trang web khác
  path: '/',
};

/** Session lưu trên Redis → mọi bản sao server dùng chung, đăng xuất có hiệu lực ngay. */
export function createSessionMiddleware(redis) {
  return session({
    name: COOKIE_NAME,
    store: new RedisStore({ client: redis, prefix: 'sess:' }),
    secret: config.SESSION_SECRETS,  // phần tử đầu để ký; các phần tử sau vẫn được chấp nhận → đổi khóa êm
    resave: false,
    saveUninitialized: false,        // chưa đăng nhập thì không tạo session, không đặt cookie
    rolling: true,                   // còn dùng thì còn gia hạn; 7 ngày không dùng thì hết hạn
    cookie: { ...cookieOptions, maxAge: SEVEN_DAYS },
  });
}

/** Hạn tuyệt đối: dù dùng liên tục, sau 30 ngày phải đăng nhập lại. */
export function absoluteTimeout(req, res, next) {
  const s = req.session;
  if (s?.userId && Date.now() - (s.createdAt ?? 0) > ABSOLUTE_MAX_MS) {
    return s.destroy(() => {
      res.clearCookie(COOKIE_NAME, cookieOptions);
      res.status(401).json({ error: 'Phiên đăng nhập đã hết hạn', code: 'SESSION_EXPIRED' });
    });
  }
  next();
}
