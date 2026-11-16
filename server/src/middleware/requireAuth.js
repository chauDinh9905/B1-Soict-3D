/** 401 nếu chưa đăng nhập. req.user do auth.loadCurrentUser gắn vào (app.js). */
export function requireAuth(req, res, next) {
  if (!req.user) return res.status(401).json({ error: 'Cần đăng nhập', code: 'UNAUTHENTICATED' });
  next();
}
