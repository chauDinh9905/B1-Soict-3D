// Các API nội dung cũ – phải trả ĐÚNG hình dạng như trước khi chuyển từ SQLite sang Postgres.
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { setup, reset, browser, query } from '../helpers.js';

let env;
before(async () => { env = await setup(); });
after(() => env.teardown());
beforeEach(reset);

test('healthz và readyz', async () => {
  const b = browser(env.base);
  assert.equal((await b.req('GET', '/healthz')).status, 200);
  assert.equal((await b.req('GET', '/readyz')).status, 200);
});

test('GET /campus giống hệt file tĩnh web/public/data/campus.json', async () => {
  const { data } = await browser(env.base).req('GET', '/api/campus');
  const expected = JSON.parse(await readFile(new URL('../../../web/public/data/campus.json', import.meta.url), 'utf8'));
  assert.deepEqual(data, expected);
});

test('GET /buildings/b1 giống hệt file tĩnh web/public/data/buildings/b1.json', async () => {
  const { data } = await browser(env.base).req('GET', '/api/buildings/b1');
  const expected = JSON.parse(await readFile(new URL('../../../web/public/data/buildings/b1.json', import.meta.url), 'utf8'));
  assert.deepEqual(
    { ...data, description: data.description ?? undefined },
    { ...expected, description: expected.description ?? undefined },
  );
});

test('tòa nhà không tồn tại -> 404 có code', async () => {
  const r = await browser(env.base).req('GET', '/api/buildings/zz');
  assert.equal(r.status, 404);
  assert.equal(r.data.code, 'NOT_FOUND');
});

test('gửi góp ý rỗng -> 400, hợp lệ -> 201', async () => {
  const b = browser(env.base);
  assert.equal((await b.req('POST', '/api/feedback', { message: '' })).status, 400);
  assert.equal((await b.req('POST', '/api/feedback', { message: 'Đẹp quá' })).status, 201);
});

test('xem góp ý: chưa đăng nhập 401; token cũ (tạm thời) vẫn được', async () => {
  const b = browser(env.base);
  assert.equal((await b.req('GET', '/api/feedback')).status, 401);
  const r = await b.req('GET', '/api/feedback', undefined, { Authorization: `Bearer ${process.env.ADMIN_TOKEN}` });
  assert.equal(r.status, 200);
});

test('đếm lượt xem nguyên tử: 20 request cùng lúc -> đúng 20', async () => {
  const b = browser(env.base);
  await Promise.all(Array.from({ length: 20 }, () => b.req('POST', '/api/stats/visit')));
  const { rows: [row] } = await query('SELECT count FROM visits WHERE day = current_date');
  assert.equal(row.count, 20);
});
