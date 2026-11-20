# B1Web – Website 3D tham quan ĐH Bách khoa Hà Nội

Bài tập lớn học phần IT4409 – Công nghệ web và dịch vụ trực tuyến.

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

## Các model 3D đã xuất (`web/public/models/buildings/b1/`)
| File `.glb` | Nội dung | Nguồn (.blend → collection) | Dựng bằng |
|---|---|---|---|
| `b1.glb` | Vỏ ngoài B1: các cánh nhà, tháp thang tròn, sảnh chính (vành, mái đón xe, cửa), mái, camera `Cam_Ref/Aerial/Lobby/Porch` (**không** gồm giảng đường) | `blender/buildings/b1/B1.blend` → `B1_Building`, loại `B1_Auditorium` | `build_b1.py` |
| `b1_sanh.glb` | **Sảnh trong** tầng 1: sảnh thông tầng, quầy lễ tân, cầu thang, thang máy, hành lang cánh nhà, camera `Cam_Sanh*` | `blender/buildings/b1/B1_Sanh.blend` → `B1_Sanh` | `build_sanh.py` |
| `b1_giangduong.glb` | **Giảng đường** tầng 3–4 trong vành: ghế bậc thang, ban công, sân khấu, bảng, camera `Cam_Aud*` | `blender/buildings/b1/B1.blend` → `B1_Auditorium` (collection con của `B1_Building`) | `build_b1.py` (cùng file với vỏ ngoài) |

Ba model **dùng chung một hệ tọa độ** (cùng `layout.py`), web gắn thẳng vào tòa nhà, không cần dịch. Khai báo trong `web/public/data/buildings/b1.json` (`model` và `interiors`); phòng trong (`sanh`, `giangduong`) nạp nền sau vỏ ngoài và có nút "Vào …" trong bảng xem model.
Khi sửa code Blender phải **xuất lại glb** và commit cùng. Lưu ý LFS: trên `origin/main` `.glb` lưu bằng git thường (commit `25678ce`), nhưng nhánh nào chưa có commit đó vẫn còn dòng `*.glb filter=lfs` trong `.gitattributes`. Gộp `origin/main` trước khi commit glb để khỏi đẩy lên dạng con trỏ LFS.

## Dựng và xuất model (chạy từ thư mục gốc repo)
```bash
# Vỏ ngoài + giảng đường: dựng một lần, xuất ra HAI glb
blender -b blender/buildings/b1/B1.blend -P blender/buildings/b1/build_b1.py --python-expr "import bpy; bpy.ops.wm.save_mainfile()"
blender -b blender/buildings/b1/B1.blend -P blender/tools/export_glb.py -- B1_Building web/public/models/buildings/b1/b1.glb exclude=B1_Auditorium
blender -b blender/buildings/b1/B1.blend -P blender/tools/export_glb.py -- B1_Auditorium web/public/models/buildings/b1/b1_giangduong.glb noextra

# Sảnh trong -> b1_sanh.glb (tự lưu B1_Sanh.blend)
blender -b blender/buildings/b1/B1_Sanh.blend -P blender/buildings/b1/build_sanh.py
blender -b blender/buildings/b1/B1_Sanh.blend -P blender/tools/export_glb.py -- B1_Sanh web/public/models/buildings/b1/b1_sanh.glb

# Render kiểm tra (không lưu .blend) -> blender/renders/
blender -b blender/buildings/b1/B1.blend -P blender/tools/render_views.py -- Cam_Ref Cam_Lobby Cam_Porch Cam_Aerial
blender -b blender/buildings/b1/B1_Sanh.blend -P blender/tools/render_views.py -- Cam_SanhEntry Cam_SanhPlan
```
Quên `exclude=` thì giảng đường bị xuất trùng vào `b1.glb`; quên `noextra` thì glb giảng đường kéo theo cả camera vỏ ngoài.
Thứ tự khi sửa sảnh/giảng đường: sửa code `blender/buildings/b1/b1/` → dựng → xuất glb → xem ảnh render. Quy ước nhóm: `.blend` chỉ một người sửa tại một thời điểm, ưu tiên sửa script Python rồi chạy lại. Ghi chú thiết kế chi tiết: `.claude/CLAUDE.md`.

## Thư mục
| Thư mục | Dùng cho | Phụ trách chính |
|---|---|---|
| `blender/` | Nguồn 3D: script dựng model, .blend, dữ liệu OSM, công cụ xuất, ảnh render kiểm tra | Làm khối |
| `web/` | Frontend (Vite + Three.js) và trang quản trị | Frontend |
| `server/` | Backend (Node.js + Express + SQLite) | Backend |
| `docs/` | Kế hoạch, quy ước, hợp đồng API, biên bản họp | Cả nhóm |
| `.claude/` | Ghi chú thiết kế mô hình B1 cho trợ lý AI | Làm khối |

Chi tiết từng phần: đọc `README.md` trong thư mục đó.
