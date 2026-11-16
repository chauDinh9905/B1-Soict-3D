import pg from 'pg';
import { config } from '../config.js';

// Một pool cho cả tiến trình. Tổng kết nối tới Postgres = số bản sao × PG_POOL_MAX → giữ nhỏ.
export const pool = new pg.Pool({ connectionString: config.DATABASE_URL, max: config.PG_POOL_MAX });

pool.on('error', (err) => console.error('[db] lỗi kết nối nhàn rỗi', err.message));

export const query = (text, params) => pool.query(text, params);

/** Chạy fn(client) trong một transaction; lỗi thì ROLLBACK và ném lại lỗi. */
export async function tx(fn) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {});
    throw err;
  } finally {
    client.release();
  }
}
