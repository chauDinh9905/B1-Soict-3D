# 004 – Chuyển CSDL từ SQLite sang PostgreSQL (thay thế 002)
**Bối cảnh:** có tài khoản người dùng và cần chạy nhiều bản sao server. SQLite là một file trên ổ đĩa của từng bản sao:
bản sao A không thấy tài khoản tạo ở bản sao B; gói host miễn phí có ổ đĩa tạm thì mất cả tài khoản khi khởi động lại.
**Quyết định:**
- Toàn bộ dữ liệu (nội dung lẫn tài khoản) chuyển sang PostgreSQL 17, truy cập bằng thư viện `pg` + SQL viết tay.
- Lược đồ quản lý bằng file `server/migrations/NNNN_*.sql`, chạy bằng `src/infra/migrate.js` (khóa `pg_advisory_lock`).
- Dev và CI dùng Postgres trong Docker (`compose.yaml`); production dùng dịch vụ Postgres được quản lý sẵn.
**Hệ quả:**
- Mọi máy phải có Docker (hoặc tự cài Postgres). Test tích hợp cần `docker compose up -d`.
- Service đổi từ gọi đồng bộ (`node:sqlite`) sang `async`. Hình dạng API không đổi (test `content.test.js` so với file tĩnh).
- Câu "không thêm thư viện mới" trong kế hoạch tải khối không còn giữ được; các bảng `areas`, `floors`, `rooms`,
  `area_links` của kế hoạch đó viết thành migration `0003_areas.sql` trên Postgres.
