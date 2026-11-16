# B1-Soict-3D – Website 3D tham quan ĐH Bách khoa Hà Nội

Bài tập lớn học phần IT4409 – Công nghệ web và dịch vụ trực tuyến.
Giai đoạn 1: khu vực quanh nhà B1. Kế hoạch: [`docs/PLAN.md`](docs/PLAN.md) · Backend: [`docs/BACKEND_PLAN.md`](docs/BACKEND_PLAN.md).

## Cần cài
Node.js LTS (≥ 22.13), Git + Git LFS, Docker (Windows: Docker Desktop bật WSL2; Linux: Docker Engine + plugin compose).

## Chạy thử (Windows và Linux giống nhau)
```bash
# 1. Hạ tầng: Postgres, Redis, Mailpit (hộp thư giả: http://localhost:8025)
docker compose up -d

# 2. Backend – terminal thứ nhất
cd server
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
npm install
npm run seed                  # tạo bảng + nạp nội dung từ web/public/data
npm run dev                   # http://localhost:3000/readyz

# 3. Frontend – terminal thứ hai
cd web
npm install
npm run dev                   # http://localhost:5173 (gọi /api qua proxy sang :3000)
```
Frontend vẫn chạy được khi chưa bật backend (dùng dữ liệu tĩnh), nhưng khi đó không có đăng nhập.

Tạo tài khoản admin đầu tiên: đăng ký trên web, rồi `cd server && npm run make-admin -- email@cua-ban.com`.

Chạy test backend: `cd server && cp .env.test.example .env.test && npm test` (cần `docker compose up -d`).

Chạy cả API trong Docker: `cp server/.env.docker.example server/.env.docker && docker compose --profile full up --build`.

## Dựng và xuất model (chạy từ thư mục gốc repo)
```bash
blender -b blender/buildings/b1/B1.blend -P blender/buildings/b1/build_b1.py
blender -b blender/buildings/b1/B1.blend -P blender/tools/export_glb.py -- B1_OSM web/public/models/buildings/b1/b1.glb
```

## Thư mục
| Thư mục | Dùng cho |
|---|---|
| `blender/` | Nguồn 3D: script dựng model, .blend, dữ liệu OSM, công cụ xuất |
| `web/` | Frontend (Vite + Three.js) và trang quản trị |
| `server/` | Backend (Node.js + Express + PostgreSQL + Redis) |
| `compose.yaml`, `deploy/` | Docker compose cho dev; (sau này) k6, Kubernetes |
| `docs/` | Kế hoạch, quy ước, hợp đồng API, quyết định kỹ thuật |
| `.claude/` | Ghi chú thiết kế mô hình B1 cho trợ lý AI |
