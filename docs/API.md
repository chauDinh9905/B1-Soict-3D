# Hợp đồng API (frontend ↔ backend)

Gốc: `/api`. Dữ liệu JSON, UTF-8. Lỗi luôn có dạng `{ "error": "thông báo" }`.
API đánh dấu 🔒 cần header `Authorization: Bearer <ADMIN_TOKEN>`.

**Quy tắc:** muốn đổi hình dạng dữ liệu → sửa file này trong Pull Request trước, cả frontend lẫn backend đồng ý rồi mới code.
Hình dạng `GET /campus` và `GET /buildings/:id` phải **giống hệt** file JSON tĩnh trong `web/public/data/` (frontend dùng chung code cho cả hai).

| Phương thức | Đường dẫn | Mô tả | Trạng thái |
|---|---|---|---|
| GET | `/health` | Kiểm tra server sống | xong |
| GET | `/campus` | `{ name, buildings: ["b1"] }` | xong |
| GET | `/buildings/:id` | Thông tin một tòa nhà + danh sách POI (xem dưới) | xong |
| PUT 🔒 | `/buildings/:id` | Sửa tên, mô tả | TODO |
| POST 🔒 | `/pois` | Thêm điểm thông tin | TODO |
| PUT 🔒 | `/pois/:id` | Sửa điểm thông tin | TODO |
| DELETE 🔒 | `/pois/:id` | Xóa điểm thông tin | TODO |
| POST | `/feedback` | Gửi góp ý `{ name?, message, poiId? }` → `201 { id }` | xong |
| GET 🔒 | `/feedback` | 200 góp ý mới nhất | xong |
| POST | `/stats/visit` | Đếm một lượt truy cập → `204` | xong |
| GET 🔒 | `/stats` | Lượt truy cập theo ngày (60 ngày) | xong |

## `GET /buildings/b1`
```json
{
  "id": "b1",
  "name": "Nhà B1",
  "model": "models/buildings/b1/b1.glb",
  "origin": { "lat": 21.004556536, "lon": 105.846622104 },
  "rotationDeg": 0,
  "placeholder": { "size": [70, 35, 50] },
  "description": "…",
  "pois": [
    { "id": "b1-sanh", "title": "Sảnh chính B1", "position": [0, 2, -25], "text": "…", "image": null }
  ],
  "views": ["Cam_Ref", "Cam_Aerial", "Cam_Lobby", "Cam_Porch"],
  "interiors": [
    { "id": "sanh", "name": "Sảnh B1", "model": "models/buildings/b1/b1_sanh.glb", "entry": "Cam_SanhEntry" },
    { "id": "giangduong", "name": "Giảng đường B1", "model": "models/buildings/b1/b1_giangduong.glb", "entry": "Cam_AudRear" }
  ]
}
```
`position` là tọa độ Three.js **cục bộ của tòa nhà** (mét; x = đông, y = lên, z = nam).

`interiors`: các phòng dựng thành model riêng (file Blender riêng, xuất `.glb` riêng). Model phòng dùng **cùng hệ
tọa độ** với `model` của tòa nhà nên web gắn thẳng vào tòa nhà, không cần dịch. `entry` là tên camera `Cam_*`
trong glb phòng, nơi người xem được đưa tới khi bấm "Vào …". Không có phòng nào thì là `[]`.
