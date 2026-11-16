// Đọc và KIỂM TRA biến môi trường một lần khi khởi động. Thiếu hoặc sai là dừng ngay, kèm thông báo rõ.
// Mọi biến mới phải được thêm vào đây VÀ vào .env.example.
import { z } from 'zod';

const list = (s) => s.split(',').map((x) => x.trim()).filter(Boolean);

const schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().positive().default(3000),
  DATABASE_URL: z.string().min(1, 'Thiếu DATABASE_URL'),
  PG_POOL_MAX: z.coerce.number().int().min(1).max(50).default(10),
  REDIS_URL: z.string().min(1, 'Thiếu REDIS_URL'),
  SESSION_SECRETS: z
    .string()
    .min(1, 'Thiếu SESSION_SECRETS')
    .refine((s) => list(s).every((k) => k.length >= 32), 'Mỗi khóa trong SESSION_SECRETS cần ít nhất 32 ký tự'),
  TRUST_PROXY: z.string().default('loopback'),
  APP_ORIGINS: z.string().default('http://localhost:5173'),
  RUN_MIGRATIONS: z.enum(['true', 'false']).default('false'),
  CONTENT_DIR: z.string().default('../web/public/data'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace', 'silent']).default('info'),
  // TẠM THỜI: chuỗi quản trị cũ, còn chấp nhận đến khi trang admin chuyển sang đăng nhập (tuần 8) rồi XÓA.
  ADMIN_TOKEN: z.string().optional(),
});

function load() {
  const parsed = schema.safeParse(process.env);
  if (!parsed.success) {
    console.error('Cấu hình môi trường không hợp lệ (xem server/.env.example):');
    for (const issue of parsed.error.issues) console.error(`  - ${issue.path.join('.')}: ${issue.message}`);
    process.exit(1);
  }
  const e = parsed.data;
  const trustProxy = /^\d+$/.test(e.TRUST_PROXY)
    ? Number(e.TRUST_PROXY)
    : e.TRUST_PROXY === 'true' ? true : e.TRUST_PROXY === 'false' ? false : e.TRUST_PROXY;
  return Object.freeze({
    ...e,
    isProd: e.NODE_ENV === 'production',
    SESSION_SECRETS: list(e.SESSION_SECRETS),
    APP_ORIGINS: list(e.APP_ORIGINS),
    RUN_MIGRATIONS: e.RUN_MIGRATIONS === 'true',
    TRUST_PROXY: trustProxy,
    ADMIN_TOKEN: e.ADMIN_TOKEN || null,
  });
}

export const config = load();
