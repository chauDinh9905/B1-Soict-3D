import { test } from 'node:test';
import assert from 'node:assert/strict';
import { hashPassword, verifyPassword } from '../../src/shared/password.js';

test('băm rồi kiểm tra đúng mật khẩu', async () => {
  const h = await hashPassword('mot-mat-khau-dai');
  assert.match(h, /^scrypt\$32768\$8\$3\$/);
  assert.deepEqual(await verifyPassword('mot-mat-khau-dai', h), { ok: true, needsRehash: false });
});

test('sai mật khẩu -> ok false', async () => {
  const h = await hashPassword('mot-mat-khau-dai');
  assert.equal((await verifyPassword('mot-mat-khau-khac', h)).ok, false);
});

test('hai lần băm cùng mật khẩu cho kết quả khác nhau (salt ngẫu nhiên)', async () => {
  assert.notEqual(await hashPassword('giong-nhau-123'), await hashPassword('giong-nhau-123'));
});

test('hash với tham số cũ -> cần băm lại', async () => {
  const old = await hashPassword('mat-khau-cu-123', { N: 2 ** 14, r: 8, p: 1 });
  assert.deepEqual(await verifyPassword('mat-khau-cu-123', old), { ok: true, needsRehash: true });
});

test('hash hỏng hoặc lạ -> không ném lỗi, coi như sai', async () => {
  for (const bad of [null, '', 'abc', 'bcrypt$x$y$z$w$v', 'scrypt$1$1$1$!!$!!']) {
    assert.equal((await verifyPassword('gi-cung-duoc', bad)).ok, false);
  }
});

test('chuẩn hóa Unicode: cùng chữ, khác cách gõ dấu vẫn khớp', async () => {
  const composed = 'mật khẩu tiếng việt';                 // dấu dựng sẵn
  const decomposed = composed.normalize('NFD');            // dấu tổ hợp
  const h = await hashPassword(composed);
  assert.equal((await verifyPassword(decomposed, h)).ok, true);
});
