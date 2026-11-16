import { createClient } from 'redis';
import { config } from '../config.js';

// Một client cho cả tiến trình: session, bộ đếm rate limit, danh sách thiết bị của user.
export const redis = createClient({ url: config.REDIS_URL });
redis.on('error', (err) => console.error('[redis]', err.message));

export async function connectRedis() {
  if (!redis.isOpen) await redis.connect();
  return redis;
}
