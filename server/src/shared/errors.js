/** Lỗi có chủ đích: status HTTP + mã cho frontend + thông báo cho người dùng. */
export class AppError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

/** Giữ tương thích với code cũ: httpError(404, 'Không có tòa nhà này'). */
export function httpError(status, message) {
  const codes = { 400: 'BAD_REQUEST', 401: 'UNAUTHENTICATED', 403: 'FORBIDDEN', 404: 'NOT_FOUND', 409: 'CONFLICT' };
  return new AppError(status, codes[status] ?? 'ERROR', message);
}
