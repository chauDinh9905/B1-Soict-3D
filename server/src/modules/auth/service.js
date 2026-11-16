// TẦNG NGHIỆP VỤ: quy tắc đăng ký / đăng nhập / phiên. Không biết gì về đường dẫn HTTP.
import { AppError } from '../../shared/errors.js';
import { hashPassword, verifyPassword, DUMMY_HASH } from '../../shared/password.js';
import { ABSOLUTE_MAX_MS, COOKIE_NAME, cookieOptions } from '../../middleware/session.js';
import * as repo from './repository.js';

const INVALID = () => new AppError(401, 'INVALID_CREDENTIALS', 'Email hoặc mật khẩu không đúng');
const sessionsKey = (userId) => `user:sessions:${userId}`;

/** Dữ liệu user gửi cho trình duyệt – KHÔNG BAO GIỜ có password_hash. */
export function toPublicUser(u) {
  return {
    id: u.id,
    email: u.email,
    displayName: u.display_name,
    role: u.role,
    emailVerified: Boolean(u.email_verified_at),
  };
}

export async function register({ email, password, displayName }) {
  const passwordHash = await hashPassword(password);
  const user = await repo.insertUser({ email, passwordHash, displayName });
  if (!user) throw new AppError(409, 'EMAIL_TAKEN', 'Email này đã được dùng để đăng ký');
  return user;
}

export async function login({ email, password, ip, userAgent }) {
  const user = await repo.findByEmail(email);
  if (!user || !user.password_hash) {
    await verifyPassword(password, DUMMY_HASH);          // tốn thời gian như thật → không lộ email có tồn tại không
    await repo.logLoginEvent({ email, success: false, reason: 'unknown_email', ip, userAgent });
    throw INVALID();
  }
  const { ok, needsRehash } = await verifyPassword(password, user.password_hash);
  if (!ok) {
    await repo.logLoginEvent({ userId: user.id, email, success: false, reason: 'bad_password', ip, userAgent });
    throw INVALID();
  }
  await repo.markLogin(user.id, needsRehash ? await hashPassword(password) : null);
  await repo.logLoginEvent({ userId: user.id, email, success: true, reason: 'ok', ip, userAgent });
  return user;
}

const promisifySession = (fn) => new Promise((ok, fail) => fn((err) => (err ? fail(err) : ok())));

/** Tạo session MỚI (chống session fixation) và ghi nhận thiết bị vào danh sách của user. */
export async function establishSession(req, redis, user) {
  await promisifySession((cb) => req.session.regenerate(cb));
  req.session.userId = user.id;
  req.session.createdAt = Date.now();
  req.session.userAgent = req.get('user-agent')?.slice(0, 200) ?? null;
  await promisifySession((cb) => req.session.save(cb));
  const key = sessionsKey(user.id);
  await redis.sAdd(key, req.sessionID);
  await redis.pExpire(key, ABSOLUTE_MAX_MS);
}

export async function endSession(req, res, redis) {
  const { userId } = req.session ?? {};
  const sid = req.sessionID;
  if (req.session) await promisifySession((cb) => req.session.destroy(cb));
  if (userId) await redis.sRem(sessionsKey(userId), sid);
  res.clearCookie(COOKIE_NAME, cookieOptions);
}

/** Đăng xuất mọi thiết bị (dùng khi đổi / đặt lại mật khẩu – giai đoạn B). */
export async function endAllSessions(redis, userId, exceptSid = null) {
  const key = sessionsKey(userId);
  const sids = await redis.sMembers(key);
  const targets = sids.filter((s) => s !== exceptSid);
  if (targets.length) await redis.del(targets.map((s) => `sess:${s}`));
  if (exceptSid && sids.includes(exceptSid)) {
    await redis.del(key);
    await redis.sAdd(key, exceptSid);
    await redis.pExpire(key, ABSOLUTE_MAX_MS);
  } else {
    await redis.del(key);
  }
}

/** Middleware: đọc user từ CSDL theo session (không lưu cả user trong session → đổi vai trò có hiệu lực ngay). */
export function loadCurrentUser(req, _res, next) {
  const userId = req.session?.userId;
  if (!userId) return next();
  repo
    .findById(userId)
    .then((u) => {
      if (u) req.user = u;
      else req.session.destroy(() => {});              // user đã bị xóa → bỏ session
      next();
    })
    .catch(next);
}
