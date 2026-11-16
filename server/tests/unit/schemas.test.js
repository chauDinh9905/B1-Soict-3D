import { test } from 'node:test';
import assert from 'node:assert/strict';
import { registerBody } from '../../src/modules/auth/schemas.js';

test('email được cắt khoảng trắng và chuyển chữ thường, giữ nguyên dấu chấm và +tag', () => {
  const r = registerBody.parse({ email: '  Sinh.Vien+b1@Gmail.COM ', password: 'mat-khau-du-dai' });
  assert.equal(r.email, 'sinh.vien+b1@gmail.com');
});

test('mật khẩu dưới 10 ký tự bị từ chối', () => {
  assert.equal(registerBody.safeParse({ email: 'a@b.vn', password: 'ngan' }).success, false);
});

test('mật khẩu trùng email bị từ chối', () => {
  assert.equal(registerBody.safeParse({ email: 'sinhvien@b1.vn', password: 'SinhVien@b1.vn' }).success, false);
});

test('email sai dạng bị từ chối', () => {
  assert.equal(registerBody.safeParse({ email: 'khong-phai-email', password: 'mat-khau-du-dai' }).success, false);
});
