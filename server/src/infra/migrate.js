// Chạy các file server/migrations/NNNN_ten.sql theo thứ tự, mỗi file một transaction.
// File đã chạy được ghi vào bảng schema_migrations. KHÔNG sửa file đã merge vào main – viết file mới.
// pg_advisory_lock bảo đảm nhiều bản sao khởi động cùng lúc cũng chỉ một bản sao chạy migration.
import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { pool } from './db.js';

const DIR = new URL('../../migrations/', import.meta.url);
const LOCK_ID = 727274; // số bất kỳ, cố định cho dự án

export async function migrate(log = console) {
  const client = await pool.connect();
  try {
    await client.query('SELECT pg_advisory_lock($1)', [LOCK_ID]);
    await client.query(`CREATE TABLE IF NOT EXISTS schema_migrations (
      name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())`);
    const done = new Set((await client.query('SELECT name FROM schema_migrations')).rows.map((r) => r.name));
    const files = (await readdir(DIR)).filter((f) => /^\d{4}_[\w-]+\.sql$/.test(f)).sort();
    for (const file of files) {
      if (done.has(file)) continue;
      const sql = await readFile(new URL(file, DIR), 'utf8');
      await client.query('BEGIN');
      try {
        await client.query(sql);
        await client.query('INSERT INTO schema_migrations (name) VALUES ($1)', [file]);
        await client.query('COMMIT');
        log.info(`[migrate] đã chạy ${file}`);
      } catch (err) {
        await client.query('ROLLBACK');
        throw new Error(`Migration ${file} lỗi: ${err.message}`);
      }
    }
  } finally {
    await client.query('SELECT pg_advisory_unlock($1)', [LOCK_ID]).catch(() => {});
    client.release();
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  migrate()
    .then(() => console.log('[migrate] xong'))
    .catch((err) => { console.error(err.message); process.exitCode = 1; })
    .finally(() => pool.end());
}
