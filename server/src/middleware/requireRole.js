import { config } from '../config.js';

/**
 * 401 nếu chưa đăng nhập, 403 nếu sai vai trò.
 * TẠM THỜI (đến tuần 8): với vai trò 'admin', vẫn chấp nhận header Authorization: Bearer <ADMIN_TOKEN> cũ
 * để trang quản trị cũ không hỏng trong lúc chuyển. Xóa nhánh này cùng biến ADMIN_TOKEN khi xong.
 */
export function requireRole(role) {
  return (req, res, next) => {
    if (role === 'admin' && config.ADMIN_TOKEN) {
      const token = (req.get('authorization') ?? '').replace(/^Bearer\s+/i, '');
      if (token && token === config.ADMIN_TOKEN) return next();
    }
    if (!req.user) return res.status(401).json({ error: 'Cần đăng nhập', code: 'UNAUTHENTICATED' });
    if (req.user.role !== role) return res.status(403).json({ error: 'Không có quyền', code: 'FORBIDDEN' });
    next();
  };
}
