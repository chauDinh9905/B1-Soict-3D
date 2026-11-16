import { z } from 'zod';
import { email, password, displayName } from '../../shared/schemas.js';

export const registerBody = z
  .object({ email, password, displayName: displayName.optional() })
  .refine((b) => b.password.trim().toLowerCase() !== b.email, {
    message: 'Mật khẩu không được trùng email',
    path: ['password'],
  });

// Đăng nhập: chỉ kiểm tra hình dạng, KHÔNG báo "mật khẩu quá ngắn" (tránh lộ quy tắc, tránh khóa người dùng cũ).
export const loginBody = z.object({
  email: z.string().trim().toLowerCase().max(254),
  password: z.string().min(1).max(128),
});
