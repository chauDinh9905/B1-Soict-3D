import { config } from './config.js';
import { logger } from './infra/logger.js';
import { pool } from './infra/db.js';
import { redis, connectRedis } from './infra/redis.js';
import { migrate } from './infra/migrate.js';
import { createApp } from './app.js';

await connectRedis();
if (config.RUN_MIGRATIONS) await migrate(logger);

const server = createApp({ redis }).listen(config.PORT, () => {
  logger.info({ port: config.PORT }, `API chạy ở http://localhost:${config.PORT}/readyz`);
  if (config.ADMIN_TOKEN) logger.warn('ADMIN_TOKEN cũ vẫn đang bật – xóa sau khi trang quản trị chuyển sang đăng nhập.');
});

// Tắt êm: ngừng nhận request mới, chờ request đang chạy xong, rồi đóng kết nối. Bắt buộc khi nhân bản / cập nhật.
let closing = false;
function shutdown(signal) {
  if (closing) return;
  closing = true;
  logger.info({ signal }, 'Đang tắt…');
  server.close(async () => {
    await Promise.allSettled([pool.end(), redis.quit()]);
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 10_000).unref();
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
