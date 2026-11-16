import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setup, reset, browser, query, redis, PASSWORD } from '../helpers.js';
import { endAllSessions } from '../../src/modules/auth/service.js';

let env;
before(async () => { env = await setup(); });
after(() => env.teardown());
beforeEach(reset);

const register = (b, email = 'sv@gmail.com', password = PASSWORD) =>
  b.req('POST', '/api/auth/register', { email, password, displayName: 'Sinh viên' });

test('đăng ký -> 201, cookie HttpOnly + SameSite=Lax, không lộ password_hash, /me trả đúng user', async () => {
  const b = browser(env.base);
  const r = await register(b);
  assert.equal(r.status, 201);
  const sid = r.setCookie.find((c) => c.startsWith('sid='));
  assert.match(sid, /HttpOnly/i);
  assert.match(sid, /SameSite=Lax/i);
  assert.deepEqual(Object.keys(r.data.user).sort(), ['displayName', 'email', 'emailVerified', 'id', 'role']);
  const me = await b.req('GET', '/api/auth/me');
  assert.equal(me.status, 200);
  assert.equal(me.data.user.email, 'sv@gmail.com');
  assert.equal(me.data.user.role, 'user');
});

test('email trùng (khác hoa/thường) -> 409 EMAIL_TAKEN', async () => {
  await register(browser(env.base), 'sv@gmail.com');
  const r = await register(browser(env.base), '  SV@Gmail.com ');
  assert.equal(r.status, 409);
  assert.equal(r.data.code, 'EMAIL_TAKEN');
});

test('hai người đăng ký cùng một email CÙNG LÚC -> đúng một người thành công', async () => {
  const results = await Promise.all([register(browser(env.base)), register(browser(env.base))]);
  assert.deepEqual(results.map((r) => r.status).sort(), [201, 409]);
  const { rows } = await query("SELECT count(*)::int AS n FROM users WHERE lower(email) = 'sv@gmail.com'");
  assert.equal(rows[0].n, 1);
});

test('đầu vào sai -> 400 VALIDATION', async () => {
  for (const body of [
    { email: 'khong-phai-email', password: PASSWORD },
    { email: 'a@b.vn', password: 'ngan' },
    { email: 'a@b.vn', password: 'a@b.vn' },
  ]) {
    const r = await browser(env.base).req('POST', '/api/auth/register', body);
    assert.equal(r.status, 400, JSON.stringify(body));
    assert.equal(r.data.code, 'VALIDATION');
  }
});

test('đăng nhập tạo session id MỚI (chống session fixation)', async () => {
  const b = browser(env.base);
  await register(b);
  const before = b.sid;
  const r = await b.req('POST', '/api/auth/login', { email: 'sv@gmail.com', password: PASSWORD });
  assert.equal(r.status, 200);
  assert.notEqual(b.sid, before);
  assert.equal((await b.req('GET', '/api/auth/me')).status, 200);
});

test('sai mật khẩu và email không tồn tại -> cùng 401, cùng thông báo', async () => {
  await register(browser(env.base));
  const wrong = await browser(env.base).req('POST', '/api/auth/login', { email: 'sv@gmail.com', password: 'sai-mat-khau-roi' });
  const unknown = await browser(env.base).req('POST', '/api/auth/login', { email: 'khong-co@gmail.com', password: 'sai-mat-khau-roi' });
  assert.equal(wrong.status, 401);
  assert.equal(unknown.status, 401);
  assert.deepEqual(wrong.data, unknown.data);
  const { rows } = await query('SELECT reason FROM login_events ORDER BY id');
  assert.deepEqual(rows.map((r) => r.reason), ['bad_password', 'unknown_email']);
});

test('thử sai lần thứ 6 trong 15 phút -> 429', async () => {
  await register(browser(env.base));
  const b = browser(env.base);
  const statuses = [];
  for (let i = 0; i < 6; i++) {
    statuses.push((await b.req('POST', '/api/auth/login', { email: 'sv@gmail.com', password: 'sai-mat-khau-roi' })).status);
  }
  assert.deepEqual(statuses, [401, 401, 401, 401, 401, 429]);
});

test('đăng xuất -> 204; cookie cũ dùng lại cũng không vào được (session đã xóa trên Redis)', async () => {
  const b = browser(env.base);
  await register(b);
  const oldCookie = b.cookie;
  assert.equal((await b.req('POST', '/api/auth/logout')).status, 204);
  assert.equal(b.cookie, null);
  assert.equal((await b.req('GET', '/api/auth/me')).status, 401);
  b.cookie = oldCookie;
  assert.equal((await b.req('GET', '/api/auth/me')).status, 401);
});

test('chống CSRF: thiếu Origin / Origin lạ -> 403; body không phải JSON -> 415', async () => {
  const b = browser(env.base);
  const body = { email: 'sv@gmail.com', password: PASSWORD };
  assert.equal((await b.req('POST', '/api/auth/register', body, { Origin: 'https://trang-xau.example' })).status, 403);
  const noOrigin = await fetch(`${env.base}/api/auth/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  assert.equal(noOrigin.status, 403);
  const text = await b.req('POST', '/api/auth/register', 'email=sv', { 'Content-Type': 'text/plain' });
  assert.equal(text.status, 415);
});

test('phân quyền: user thường 403; được cấp admin -> có hiệu lực NGAY, không cần đăng nhập lại', async () => {
  const b = browser(env.base);
  await register(b);
  assert.equal((await b.req('GET', '/api/feedback')).status, 403);
  await query("UPDATE users SET role = 'admin' WHERE email = 'sv@gmail.com'");
  assert.equal((await b.req('GET', '/api/feedback')).status, 200);
});

test('quá hạn tuyệt đối 30 ngày -> 401 SESSION_EXPIRED', async () => {
  const b = browser(env.base);
  await register(b);
  const key = `sess:${b.sid}`;
  const sess = JSON.parse(await redis.get(key));
  sess.createdAt = Date.now() - 31 * 24 * 60 * 60 * 1000;
  await redis.set(key, JSON.stringify(sess), { KEEPTTL: true });
  const r = await b.req('GET', '/api/auth/me');
  assert.equal(r.status, 401);
  assert.equal(r.data.code, 'SESSION_EXPIRED');
});

test('đăng xuất mọi thiết bị khác (dùng cho đổi mật khẩu ở giai đoạn B)', async () => {
  const phone = browser(env.base);
  const laptop = browser(env.base);
  const { data } = await register(phone);
  await laptop.req('POST', '/api/auth/login', { email: 'sv@gmail.com', password: PASSWORD });
  await endAllSessions(redis, data.user.id, phone.sid);
  assert.equal((await phone.req('GET', '/api/auth/me')).status, 200);
  assert.equal((await laptop.req('GET', '/api/auth/me')).status, 401);
});

test('góp ý khi đã đăng nhập được gắn với tài khoản', async () => {
  const b = browser(env.base);
  const { data } = await register(b);
  await b.req('POST', '/api/feedback', { message: 'Thêm ảnh sảnh nhé' });
  const { rows } = await query('SELECT user_id FROM feedback');
  assert.equal(rows[0].user_id, data.user.id);
});
