// Băm mật khẩu bằng scrypt có sẵn trong Node – không cần thư viện native, chạy như nhau trên Windows/Linux/Docker.
// Định dạng: scrypt$N$r$p$salt$hash  → tự mô tả, đổi tham số hay đổi thuật toán sau này không phải ép đặt lại mật khẩu.
import { scrypt as scryptCb, randomBytes, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';

const scrypt = promisify(scryptCb);
// Một trong các bộ tham số scrypt OWASP liệt kê: N=2^15, r=8, p=3 (~32 MiB RAM mỗi lần băm).
export const CURRENT = Object.freeze({ N: 2 ** 15, r: 8, p: 3 });
const MAXMEM = 64 * 1024 * 1024;
const KEYLEN = 32;

const prep = (pw) => String(pw).normalize('NFKC');

export async function hashPassword(pw, params = CURRENT) {
  const salt = randomBytes(16);
  const key = await scrypt(prep(pw), salt, KEYLEN, { ...params, maxmem: MAXMEM });
  return ['scrypt', params.N, params.r, params.p, salt.toString('base64url'), key.toString('base64url')].join('$');
}

/** Trả { ok, needsRehash }. Không bao giờ ném lỗi vì hash hỏng – coi như sai mật khẩu. */
export async function verifyPassword(pw, stored) {
  const parts = String(stored ?? '').split('$');
  if (parts.length !== 6 || parts[0] !== 'scrypt') return { ok: false, needsRehash: false };
  const [, N, r, p, salt, hash] = parts;
  try {
    const expected = Buffer.from(hash, 'base64url');
    const actual = await scrypt(prep(pw), Buffer.from(salt, 'base64url'), expected.length,
      { N: Number(N), r: Number(r), p: Number(p), maxmem: MAXMEM });
    const ok = actual.length === expected.length && timingSafeEqual(actual, expected);
    const needsRehash = ok && (Number(N) !== CURRENT.N || Number(r) !== CURRENT.r || Number(p) !== CURRENT.p);
    return { ok, needsRehash };
  } catch {
    return { ok: false, needsRehash: false };
  }
}

// Dùng khi email không tồn tại, để thời gian trả lời giống khi sai mật khẩu (không lộ email nào đã đăng ký).
export const DUMMY_HASH = await hashPassword(randomBytes(16).toString('hex'));
