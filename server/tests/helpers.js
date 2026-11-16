// Dựng server thật trên Postgres + Redis thật (từ docker compose) cho test tích hợp.
import { pool, query } from '../src/infra/db.js';
import { redis, connectRedis } from '../src/infra/redis.js';
import { migrate } from '../src/infra/migrate.js';
import { seed } from '../src/db/seed.js';
import { createApp } from '../src/app.js';

export const ORIGIN = 'http://localhost:5173';
export { query, redis };

export async function setup() {
  try {
    await query('SELECT 1');
  } catch (err) {
    throw new Error(`Không kết nối được Postgres test (${err.message}). Đã chạy "docker compose up -d" và tạo server/.env.test chưa?`);
  }
  await connectRedis();
  await migrate({ info() {} });
  await query('TRUNCATE users, login_events, outbox, auth_tokens, oauth_accounts, feedback, visits RESTART IDENTITY CASCADE');
  await seed();
  await redis.flushDb();
  const server = createApp({ redis }).listen(0);
  await new Promise((ok) => server.once('listening', ok));
  return {
    base: `http://127.0.0.1:${server.address().port}`,
    async teardown() {
      server.closeAllConnections();
      await new Promise((ok) => server.close(ok));
      await Promise.allSettled([pool.end(), redis.quit()]);
    },
  };
}

/** Xóa dữ liệu người dùng + bộ đếm rate limit giữa các test (giữ nguyên nội dung đã seed). */
export async function reset() {
  await query('TRUNCATE users, login_events, feedback, visits RESTART IDENTITY CASCADE');
  await redis.flushDb();
}

/** fetch kèm "hũ cookie" đơn giản – cư xử như một trình duyệt đang mở trang. */
export function browser(base) {
  let cookie = null;
  return {
    get cookie() { return cookie; },
    set cookie(v) { cookie = v; },
    /** session id thật (cookie có dạng s:<sid>.<chữ ký>) */
    get sid() { return cookie ? decodeURIComponent(cookie.split('=')[1]).slice(2).split('.')[0] : null; },
    async req(method, path, body, headers = {}) {
      const h = { Origin: ORIGIN, ...headers };
      if (body !== undefined) h['Content-Type'] ??= 'application/json';
      if (cookie) h.Cookie = cookie;
      const payload = body === undefined ? undefined : typeof body === 'string' ? body : JSON.stringify(body);
      const res = await fetch(base + path, { method, headers: h, body: payload });
      const setCookie = res.headers.getSetCookie();
      for (const c of setCookie) {
        const pair = c.split(';')[0];
        const [name, value] = pair.split('=');
        if (name === 'sid') cookie = value ? pair : null;
      }
      const text = await res.text();
      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch { data = text; }
      return { status: res.status, data, setCookie };
    },
  };
}

export const PASSWORD = 'mat-khau-du-dai-123';
