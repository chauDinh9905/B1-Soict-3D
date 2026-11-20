Mọi thứ riêng của nhà B1.

| Đường dẫn | Nội dung |
|---|---|
| `B1.blend` | Vỏ ngoài (`B1_Building`) → `b1.glb`; giảng đường (`B1_Auditorium`, nằm trong `B1_Building`) → `b1_giangduong.glb` |
| `B1_Sanh.blend` | Sảnh trong (collection `B1_Sanh`) → `b1_sanh.glb` |
| `build_b1.py`, `build_sanh.py` | Entry dựng hai file trên |
| `b1/` | Package Python: `layout` (footprint), `wings`, `lobby`, `tower`, `rooftop`, `auditorium`, `sanh`, ... |
| `ref/` | Ảnh tham chiếu, sketch |
| `textures/` | Texture dùng cho sảnh (đá hoa `marble.jpg`, tự sinh nếu thiếu) |
| `_backup/` | Bản cũ trước các lần đổi lớn |

File glb xuất ra: `web/public/models/buildings/b1/` (xem `README.md` gốc repo).
Việc giai đoạn 1: thêm collection `B1_Collision` chứa các hộp `COL_*` và các Empty `POI_*` cho hotspot.
