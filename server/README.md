# server/ – backend (Node.js + Express 5 + PostgreSQL + Redis)

Kế hoạch đầy đủ: `docs/BACKEND_PLAN.md`. Hợp đồng API: `docs/API.md`.

```
src/
  index.js            khởi động: nối Redis, (tùy chọn) chạy migration, listen, tắt êm khi SIGTERM
  app.js              tạo app Express: healthz/readyz, log, helmet, chống CSRF, session, các module
  config.js           đọc + kiểm tra biến môi trường bằng zod – thiếu là dừng ngay
  infra/              DÙNG CHUNG – kết nối ra ngoài: db (pool pg, tx), migrate, redis, logger
  middleware/         DÙNG CHUNG: session, sameOrigin, rateLimit, requireAuth, requireRole, errorHandler
  shared/             DÙNG CHUNG – hàm thuần: password (scrypt), schemas (zod), errors (AppError)
  modules/<ten>/      MODULE CHỨC NĂNG – không import lẫn nhau
    auth/             routes · service · repository · schemas  ← khuôn 3 tầng cho module mới
    campus/ buildings/ pois/ feedback/ stats/                  ← module cũ, đã chuyển sang Postgres
  db/seed.js          nạp nội dung từ web/public/data (CONTENT_DIR)
migrations/           0001_init.sql, 0002_auth.sql … – KHÔNG sửa file đã merge, viết file mới
scripts/make-admin.js cấp quyền admin cho một tài khoản đã đăng ký
tests/
  unit/               không cần CSDL: npm run test:unit
  integration/        Postgres + Redis thật từ docker compose
  helpers.js          dựng server test + "hũ cookie" giả lập trình duyệt
```

## Chạy
```bash
docker compose up -d          # ở thư mục gốc repo: postgres, redis, mailpit
cd server
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
npm install
npm run seed                  # chạy migration + nạp nội dung
npm run dev                   # http://localhost:3000/readyz
npm run make-admin -- email@cua-ban.com
```

## Test
```bash
cp .env.test.example .env.test
npm test                      # unit + integration (cần docker compose up -d)
npm run test:unit             # chỉ unit, không cần Docker
```
Đã có volume Postgres từ trước khi thêm `deploy/postgres/init` thì CSDL `tour_test` chưa tồn tại:
chạy `docker compose down -v && docker compose up -d` (xóa dữ liệu dev) hoặc
`docker compose exec postgres createdb -U tour tour_test`.

## Thêm một module mới
1. Sửa `docs/API.md` trước (PR có người frontend duyệt).
2. Bảng mới → file `migrations/NNNN_ten.sql` mới.
3. Tạo `modules/<ten>/` theo khuôn `auth/`: `schemas.js` (zod) → `routes.js` → `service.js` → `repository.js`.
4. Gắn vào `app.js`. Viết test trong `tests/integration/`.
