# 005 – Phiên đăng nhập: session ID trong cookie, lưu trên Redis (không dùng JWT)
**Bối cảnh:** một website, một backend; cần đăng xuất / đổi mật khẩu / khóa tài khoản có hiệu lực ngay; chạy nhiều bản sao.
**Quyết định:** `express-session` + `connect-redis`. Cookie `sid` chỉ chứa chuỗi ngẫu nhiên có chữ ký,
`HttpOnly`, `Secure` (production), `SameSite=Lax`. Hết hạn sau 7 ngày không dùng; hạn tuyệt đối 30 ngày.
Session chỉ lưu `userId` – thông tin user đọc từ Postgres mỗi request (đổi vai trò có hiệu lực ngay).
Mật khẩu băm bằng scrypt (`node:crypto`), định dạng tự mô tả để đổi tham số / thuật toán về sau.
**Vì sao không JWT:** không thu hồi được trước khi hết hạn nếu không thêm nơi lưu; dễ dùng sai (localStorage, thuật toán ký).
JWT hợp lý khi có app di động hoặc nhiều dịch vụ cần xác thực – chưa phải lúc này.
**Hệ quả:** cần Redis ở mọi môi trường. Frontend và API phải cùng tên miền (proxy Vite khi dev, `vercel.json` khi deploy),
nếu không cookie thành cookie bên thứ ba và bị trình duyệt chặn.
