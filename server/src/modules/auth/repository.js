// TẦNG DỮ LIỆU: chỉ câu lệnh SQL, không có quy tắc nghiệp vụ.
import { query } from '../../infra/db.js';

const COLUMNS = 'id, email, password_hash, display_name, role, email_verified_at, last_login_at, created_at';

/** Trả user mới, hoặc null nếu email đã tồn tại (ràng buộc UNIQUE quyết định – an toàn khi đăng ký đồng thời). */
export async function insertUser({ email, passwordHash, displayName }) {
  const { rows } = await query(
    `INSERT INTO users (email, password_hash, display_name) VALUES ($1, $2, $3)
     ON CONFLICT ((lower(email))) DO NOTHING
     RETURNING ${COLUMNS}`,
    [email, passwordHash, displayName ?? null],
  );
  return rows[0] ?? null;
}

export async function findByEmail(email) {
  const { rows } = await query(`SELECT ${COLUMNS} FROM users WHERE lower(email) = lower($1)`, [email]);
  return rows[0] ?? null;
}

export async function findById(id) {
  const { rows } = await query(`SELECT ${COLUMNS} FROM users WHERE id = $1`, [id]);
  return rows[0] ?? null;
}

export async function markLogin(id, newPasswordHash = null) {
  await query(
    `UPDATE users SET last_login_at = now(),
       password_hash = COALESCE($2, password_hash),
       updated_at = CASE WHEN $2::text IS NULL THEN updated_at ELSE now() END
     WHERE id = $1`,
    [id, newPasswordHash],
  );
}

export async function logLoginEvent({ userId = null, email, success, reason, ip, userAgent }) {
  await query(
    'INSERT INTO login_events (user_id, email, success, reason, ip, user_agent) VALUES ($1, $2, $3, $4, $5, $6)',
    [userId, email, success, reason, ip ?? null, userAgent?.slice(0, 300) ?? null],
  );
}
