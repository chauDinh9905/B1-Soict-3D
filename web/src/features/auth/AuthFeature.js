/**
 * Tài khoản người dùng (frontend giao diện – TV4, phối hợp backend BE1).
 * ĐÃ CHẠY: khi thế giới tải xong, hỏi backend đang đăng nhập ai và phát 'auth:changed' (user | null).
 * TODO (tuần 7):
 *  1. Nút "Đăng nhập" / tên người dùng trên toolbar; ẩn hẳn nếu ctx.api.online === false.
 *  2. Panel form đăng nhập + đăng ký bằng createPanel() (ui/components/Panel.js).
 *  3. Gọi ctx.api.login / register / logout; lỗi thì hiện res.data.error (backend đã viết sẵn tiếng Việt).
 *     res.status 429 -> "Thử quá nhiều lần"; res.offline -> "Không kết nối được máy chủ".
 *  4. Sau mỗi lần đổi trạng thái: bus.emit('auth:changed', user | null).
 *  5. KHÔNG lưu gì về đăng nhập trong localStorage – cookie HttpOnly lo toàn bộ.
 */
export class AuthFeature {
  init(ctx) {
    this.ctx = ctx;
    this.user = null;
    this.off = [
      ctx.bus.on('world:ready', async () => {
        this.user = await ctx.api.me();
        ctx.bus.emit('auth:changed', this.user);
      }),
    ];
  }
  dispose() { this.off.forEach((f) => f()); }
}
