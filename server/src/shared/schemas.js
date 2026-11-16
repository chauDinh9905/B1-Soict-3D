import { z } from 'zod';

// Email: cắt khoảng trắng, chữ thường. KHÔNG bỏ dấu chấm hay +tag của Gmail.
export const email = z.string().trim().toLowerCase().max(254).pipe(z.email({ message: 'Email không hợp lệ' }));

// Độ dài quan trọng hơn độ phức tạp: không ép chữ hoa / ký tự đặc biệt.
export const password = z
  .string()
  .min(10, 'Mật khẩu cần ít nhất 10 ký tự')
  .max(128, 'Mật khẩu tối đa 128 ký tự');

export const displayName = z.string().trim().min(1).max(60);

export const optionalText = (max) => z.string().trim().max(max).optional().transform((v) => (v ? v : null));
