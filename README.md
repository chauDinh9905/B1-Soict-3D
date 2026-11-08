<<<<<<< HEAD
# B1Web – Website 3D tham quan ĐH Bách khoa Hà Nội

Giai đoạn 1: khu vực quanh nhà B1. Kế hoạch đầy đủ: [`docs/PLAN.md`](docs/PLAN.md).

## Chạy thử (Windows và Linux giống nhau)
```bash
# Frontend – chạy được một mình
cd web
npm install
npm run dev                   # http://localhost:5173

# Backend – terminal thứ hai (không bắt buộc khi mới bắt đầu)
cd server
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
npm install
npm run seed
npm run dev                   # http://localhost:3000/api/health
```
Chưa có `web/public/models/buildings/b1/b1.glb` thì web hiện khối hộp tạm đúng vị trí B1.

## Dựng và xuất model (chạy từ thư mục gốc repo)
```bash
blender -b blender/buildings/b1/B1.blend -P blender/buildings/b1/build_b1.py
blender -b blender/buildings/b1/B1.blend -P blender/tools/export_glb.py -- B1_Building web/public/models/buildings/b1/b1.glb
```

## Thư mục
| Thư mục | Dùng cho | Phụ trách chính |
|---|---|---|
| `blender/` | Nguồn 3D: script dựng model, .blend, dữ liệu OSM, công cụ xuất | Làm khối |
| `web/` | Frontend (Vite + Three.js) và trang quản trị | Frontend |
| `server/` | Backend (Node.js + Express + SQLite) | Backend |
| `docs/` | Kế hoạch, quy ước, hợp đồng API, biên bản họp | Cả nhóm |
| `.claude/` | Ghi chú thiết kế mô hình B1 cho trợ lý AI | Làm khối |

Chi tiết từng phần: đọc `README.md` trong thư mục đó.
=======
# B1-Soict-3D
Bài tập lớn học phần IT4409 - Công nghệ web và dịch vụ trực tuyến
>>>>>>> 57505405d60e543965ef67e0c1a13248697dfee9
