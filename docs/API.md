# Hợp đồng API (frontend ↔ backend)

Gốc: `/api`. Dữ liệu JSON, UTF-8. Lỗi luôn có dạng `{ "error": "thông báo cho người dùng", "code": "MA_LOI" }` – frontend so `code`, không so chuỗi thông báo.
Lỗi kiểm tra đầu vào (`400 VALIDATION`) có thêm `fields: [{ path, message }]`.

🔐 = cần đăng nhập (cookie `sid`). 👑 = cần vai trò `admin`. Thiếu đăng nhập → `401 UNAUTHENTICATED`; sai vai trò → `403 FORBIDDEN`.
*Tạm thời đến tuần 8:* API 👑 vẫn nhận header `Authorization: Bearer <ADMIN_TOKEN>` cũ.

Mọi request **ghi dữ liệu** (khác GET) phải có header `Origin` thuộc danh sách `APP_ORIGINS` (`403 BAD_ORIGIN`), và nếu có body thì là JSON (`415`). Trình duyệt tự gửi `Origin`; công cụ như curl/k6 phải tự thêm.

**Quy tắc:** muốn đổi hình dạng dữ liệu → sửa file này trong Pull Request trước, cả frontend lẫn backend đồng ý rồi mới code.
Hình dạng `GET /campus` và `GET /buildings/:id` phải **giống hệt** file JSON tĩnh trong `web/public/data/` (frontend dùng chung code cho cả hai).

| Phương thức | Đường dẫn | Mô tả | Trạng thái |
|---|---|---|---|
| GET | `/health` | Kiểm tra server sống | xong |
| GET | `/campus` | `{ name, buildings: ["b1"] }` | xong |
| GET | `/buildings/:id` | Thông tin một tòa nhà + danh sách POI (xem dưới) | xong |
| PUT 👑 | `/buildings/:id` | Sửa tên, mô tả | TODO |
| POST 👑 | `/pois` | Thêm điểm thông tin | TODO |
| PUT 👑 | `/pois/:id` | Sửa điểm thông tin | TODO |
| DELETE 👑 | `/pois/:id` | Xóa điểm thông tin | TODO |
| POST | `/feedback` | Gửi góp ý `{ name?, message, poiId? }` → `201 { id }`; đã đăng nhập thì gắn với tài khoản | xong |
| GET 👑 | `/feedback` | 200 góp ý mới nhất | xong |
| POST | `/stats/visit` | Đếm một lượt truy cập → `204` | xong |
| GET 👑 | `/stats` | Lượt truy cập theo ngày (60 ngày) | xong |

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
  "views": ["Cam_Ref", "Cam_Aerial", "Cam_Lobby", "Cam_Porch"]
}
```
`position` là tọa độ Three.js **cục bộ của tòa nhà** (mét; x = đông, y = lên, z = nam).

## Tài khoản – `/auth`

| Phương thức | Đường dẫn | Mô tả | Thành công | Lỗi chính | Trạng thái |
|---|---|---|---|---|---|
| POST | `/auth/register` | `{ email, password, displayName? }` – tạo tài khoản **và đăng nhập luôn** | `201 { user }` + cookie | `400 VALIDATION`, `409 EMAIL_TAKEN`, `429 RATE_LIMITED` | xong |
| POST | `/auth/login` | `{ email, password }` | `200 { user }` + cookie | `401 INVALID_CREDENTIALS`, `429 RATE_LIMITED` | xong |
| POST | `/auth/logout` | Xóa session hiện tại (gọi khi chưa đăng nhập cũng được) | `204` | – | xong |
| GET | `/auth/me` 🔐 | Người đang đăng nhập | `200 { user }` | `401 UNAUTHENTICATED`, `401 SESSION_EXPIRED` | xong |
| | `/auth/verify-email`, `/auth/password/*`, `/auth/google`, `/auth/sessions` | Giai đoạn B – xem `BACKEND_PLAN.md` mục 8.1 | | | TODO |

Đối tượng `user` – **không bao giờ** có mật khẩu hay hash:
```json
{ "id": "a9ae9a9a-…", "email": "sv@gmail.com", "displayName": "Châu", "role": "user", "emailVerified": false }
```

Quy tắc:
- Email được cắt khoảng trắng và chuyển chữ thường; không phân biệt hoa/thường khi kiểm tra trùng.
- Mật khẩu 10–128 ký tự, không được trùng email. Không ép chữ hoa / ký tự đặc biệt.
- Đăng nhập sai luôn trả **cùng một** thông báo, dù email có tồn tại hay không.
- Giới hạn: đăng nhập 5 lần / 15 phút cho mỗi (IP, email) và 50 lần / 15 phút cho mỗi IP; đăng ký 5 lần / giờ cho mỗi IP.
- Cookie `sid`: `HttpOnly`, `SameSite=Lax`, `Secure` ở production; hết hạn sau 7 ngày không dùng, tối đa 30 ngày.
