# 006 – Phạm vi dùng Docker, Kubernetes, Kafka
**Bối cảnh:** nhóm đề xuất cả ba. Lượng người dùng thực tế cỡ vài chục đến vài trăm người cùng lúc; nhóm 5 sinh viên.
**Quyết định:**
- **Docker: dùng thật ngay.** `compose.yaml` cho dev (Postgres, Redis, Mailpit); `server/Dockerfile` để deploy.
- **Kubernetes: chỉ học trên máy (k3d) ở giai đoạn C (tuần 11).** Production deploy bằng host chạy Docker image.
  Không dùng ingress-nginx (đã ngừng hỗ trợ từ 3/2026); dùng Traefik có sẵn trong k3d, hướng tới Gateway API.
- **Kafka: không dùng cho đăng nhập.** Giai đoạn C dùng cho một luồng sự kiện thống kê (`telemetry.area-load.v1`).
  Email ở giai đoạn B dùng bảng outbox + worker, là cầu nối sang Kafka về sau.
**Hệ quả:** giai đoạn C chỉ bắt đầu khi Must + Should xong; thiếu thời gian thì cắt C trước. Chi tiết: BACKEND_PLAN mục 3.
