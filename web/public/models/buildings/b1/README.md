# Model B1 đã xuất

| File | Nội dung | Nguồn |
|---|---|---|
| `b1.glb` | Vỏ ngoài + camera `Cam_Ref/Aerial/Lobby/Porch` (không có giảng đường) | `blender/buildings/b1/B1.blend`, collection `B1_Building`, loại `B1_Auditorium` |
| `b1_sanh.glb` | Sảnh trong tầng 1 + camera `Cam_Sanh*` | `blender/buildings/b1/B1_Sanh.blend`, collection `B1_Sanh` |
| `b1_giangduong.glb` | Giảng đường tầng 3–4 + camera `Cam_Aud*` | `blender/buildings/b1/B1.blend`, collection `B1_Auditorium` |

Cùng hệ tọa độ, gắn thẳng vào tòa nhà. Khai báo ở `web/public/data/buildings/b1.json` (`model`, `interiors`).
Đừng sửa tay: xuất bằng `blender/tools/export_glb.py` (cần `exclude=B1_Auditorium` cho `b1.glb`, `noextra` cho giảng đường), lệnh đầy đủ ở `README.md` gốc repo.
Object tên `noCollide` (cánh cửa đôi `Lobby_F1_Doors`) cho phép đi bộ xuyên qua trên web.
