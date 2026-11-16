// Cấp quyền admin cho một tài khoản ĐÃ đăng ký. Không có API nào tự nâng quyền – chỉ script này.
//   npm run make-admin -- email@example.com
import { pool, query } from '../src/infra/db.js';

const email = process.argv[2];
if (!email) {
  console.error('Cách dùng: npm run make-admin -- email@example.com');
  process.exit(1);
}
const { rows } = await query(
  "UPDATE users SET role = 'admin', updated_at = now() WHERE lower(email) = lower($1) RETURNING email, role",
  [email.trim()],
);
if (rows.length) console.log(`Đã cấp quyền admin cho ${rows[0].email}`);
else { console.error(`Không có tài khoản ${email} – hãy đăng ký trên web trước.`); process.exitCode = 1; }
await pool.end();
