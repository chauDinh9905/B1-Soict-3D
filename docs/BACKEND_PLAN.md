# Kế hoạch triển khai Backend – Tài khoản, phiên đăng nhập và khả năng chịu tải

| | |
|---|---|
| **Dự án** | B1Web – Website 3D tham quan ĐH Bách khoa Hà Nội |
| **Phạm vi tài liệu** | Đăng ký / đăng nhập bằng email + mật khẩu, lưu phiên đăng nhập, nhiều người dùng cùng lúc; vai trò của Docker, Kubernetes, Kafka. Google để sau giai đoạn này |
| **Đặt tại** | `docs/BACKEND_PLAN.md`, đi cùng `docs/PLAN.md` và kế hoạch "Tải khối B1 theo khu vực" |
| **Ngày lập** | 16/11/2026 – đầu tuần 6, theo lịch tuần 1 = 12/10/2026 |
| **Thời lượng** | Tuần 6–11 làm, tuần 12 đệm (16/11/2026 – 03/01/2027) |

> **Tinh thần chung:** hệ thống phải **đúng và an toàn trước**, rồi mới tính đến **mở rộng được**; công nghệ chỉ thêm vào khi nó giải quyết một vấn đề thật đang có. Mỗi công nghệ mới đều có giá: phải học, phải vận hành, phải gỡ lỗi. Tài liệu này ghi rõ cái giá đó, để nhóm tự chọn có hiểu biết.

---

## Mục lục
1. Hiện trạng
2. Mục tiêu và phạm vi
3. Docker, Kubernetes, Kafka: dùng khi nào, dùng đến đâu
4. Công nghệ và cài đặt
5. Kiến trúc
6. Cấu trúc thư mục
7. Cơ sở dữ liệu
8. API
9. Phiên đăng nhập (session)
10. Bảo mật
11. Nhiều người dùng cùng lúc: tải nằm ở đâu, đo thế nào
12. Docker và docker compose
13. Kubernetes (giai đoạn C)
14. Kafka (giai đoạn C)
15. Kiểm thử và CI
16. Triển khai (deploy)
17. Thay đổi ở frontend
18. Phân công
19. Lộ trình theo tuần
20. Quy tắc làm việc
21. Rủi ro
22. Mở rộng về sau
23. Tài liệu học
24. Việc cần chốt ngay tuần này

---

## 1. Hiện trạng

### 1.1 Backend đang có

Backend dùng Express 5 + SQLite (`node:sqlite`), test bằng `node:test`. Các module hiện có: `campus`, `buildings`, `pois` (khung, trả `501`), `feedback`, `stats`.

Kế hoạch "Tải khối B1 theo khu vực" của Nam bổ sung thêm `areas`, `rooms` và script `manifest`.

Quyền quản trị hiện là **một chuỗi `ADMIN_TOKEN` dùng chung**. Chưa có khái niệm người dùng hay tài khoản.

### 1.2 Vì sao cần thay đổi nền tảng dữ liệu

Có tài khoản người dùng và chạy **nhiều bản sao server cùng lúc** thì SQLite không còn phù hợp:

| Vấn đề | Với SQLite | Với PostgreSQL |
|---|---|---|
| Nhiều bản sao server (2 container, 2 pod) | Mỗi bản sao có **file CSDL riêng**. Người đăng ký ở bản sao A không đăng nhập được ở bản sao B | Mọi bản sao dùng chung một CSDL |
| Ghi đồng thời (đăng ký, góp ý, thống kê) | Mỗi lúc chỉ một luồng ghi | Ghi đồng thời, có khóa theo dòng |
| Deploy trên gói miễn phí có ổ đĩa tạm | Mất file khi khởi động lại → **mất tài khoản người dùng** | Dịch vụ Postgres được quản lý sẵn, dữ liệu bền vững |
| Ràng buộc email không trùng khi hai người đăng ký cùng lúc | Được, nhưng chỉ trong một file | Được, trên toàn hệ thống |

Kết luận: **chuyển toàn bộ sang PostgreSQL**. Không chạy song song hai CSDL, vì như vậy gấp đôi việc vận hành.

Dữ liệu nội dung (tòa nhà, khối, phòng, POI) vốn sinh từ JSON bằng `npm run seed`, nên chuyển sang Postgres rất ít rủi ro. Quyết định này thay cho `docs/decisions/002` (xem mục 24).

### 1.3 Cần ghi nhận

Kế hoạch của Nam có câu "Không thêm thư viện mới". Kế hoạch này **buộc phải thêm** thư viện và hạ tầng (Postgres, Redis, thư viện session). Hai kế hoạch phải được cả nhóm backend thống nhất trước khi code (mục 24).

---

## 2. Mục tiêu và phạm vi

**Mục tiêu sản phẩm**

- Người tham quan tạo được tài khoản bằng email và mật khẩu, đăng nhập, và vẫn giữ trạng thái đăng nhập khi đóng rồi mở lại trình duyệt.
- Quản trị viên đăng nhập bằng tài khoản có vai trò `admin`, thay cho chuỗi token dùng chung.
- Hệ thống phục vụ được nhiều người cùng lúc mà không mất phiên và không lỗi dữ liệu.

**Mục tiêu học tập**

- Hiểu xác thực và phiên đăng nhập ở mức "làm đúng như ngoài thực tế": băm mật khẩu, cookie an toàn, chống dò mật khẩu.
- Hiểu "server không giữ trạng thái" (stateless) và vì sao nhờ đó mới nhân bản server được.
- Đóng gói bằng Docker, đo tải bằng số liệu thật.
- Biết Kubernetes và Kafka giải quyết vấn đề gì, và **khi nào chưa cần đến chúng**.

| Mức | Tính năng | Hạ tầng |
|---|---|---|
| **Must** | Đăng ký, đăng nhập, đăng xuất, `GET /me` · Băm mật khẩu bằng scrypt · Session lưu trên Redis, cookie `httpOnly` · Giới hạn số lần thử đăng nhập · Vai trò `user` / `admin` thay `ADMIN_TOKEN` · Chuyển CSDL sang PostgreSQL | Docker compose cho môi trường dev (Postgres, Redis, Mailpit) · Deploy backend + Postgres + Redis · Vercel chuyển tiếp `/api` để cookie là cookie cùng trang |
| **Should** | Xác thực email · Quên / đặt lại mật khẩu · Xem và đăng xuất các thiết bị khác · Đổi mật khẩu, xóa tài khoản | Hàng đợi email bằng bảng outbox + tiến trình worker · Đo tải bằng k6 · CI chạy test với Postgres và Redis thật |
| **Could** | Gắn góp ý với tài khoản · Lịch sử đăng nhập cho quản trị | **Kubernetes chạy trên máy (k3d)** · **Kafka cho luồng sự kiện thống kê** · Đo đạc bằng Prometheus |
| **Won't** (giai đoạn này) | Xác thực hai lớp (2FA), đăng nhập không mật khẩu (passkey) · Nhiều vai trò chi tiết · Tách microservice | Kubernetes trên cloud thật · Kafka trên môi trường production |

---

## 3. Docker, Kubernetes, Kafka: dùng khi nào, dùng đến đâu

Phần này là đánh giá thẳng thắn của tài liệu. Nhóm đề xuất cả ba công nghệ. Cả ba đều đáng học, nhưng **không phải cả ba đều đáng đưa vào sản phẩm** ở quy mô này.

### 3.1 Đánh giá

| | Giải quyết vấn đề gì | Dự án này có vấn đề đó không? | Giá phải trả | Kết luận |
|---|---|---|---|---|
| **Docker** | "Máy em chạy được mà": đóng gói server cùng môi trường chạy, giống nhau trên Windows, Linux và host | **Có ngay**: nhóm dùng cả Windows lẫn Linux, cần Postgres và Redis giống nhau trên mọi máy | Thấp. Học 1–2 buổi; Windows cần WSL2 | **Dùng ngay** (giai đoạn A) |
| **Kubernetes** | Điều phối **nhiều** container trên **nhiều** máy: tự khởi động lại khi chết, tự nhân bản theo tải, cập nhật không gián đoạn | **Chưa**: lượng người dùng thực tế cỡ vài chục đến vài trăm, một hoặc hai container là đủ. Host kiểu Render/Railway/Fly đã tự khởi động lại và nhân bản | **Cao**: nhiều khái niệm (Pod, Deployment, Service, Ingress/Gateway, Secret, HPA). Cụm trên cloud tốn tiền; gói miễn phí rất hạn chế | **Học trên máy bằng k3d** ở giai đoạn C. Sản phẩm thật vẫn deploy trên host đơn giản |
| **Kafka** | Luồng sự kiện **lưu lâu, đọc lại được, nhiều bên tiêu thụ**, lưu lượng rất lớn (hàng nghìn đến hàng triệu sự kiện/giây) | **Không cho đăng nhập**: đăng nhập là yêu cầu–trả lời đồng bộ, đưa qua Kafka chỉ làm chậm và phức tạp hơn. **Có một chỗ hợp lý**: luồng sự kiện thống kê (thời gian tải khối, lượt xem) | **Cao**: thêm một hệ phân tán phải vận hành; thư viện Node.js phổ biến nhất (KafkaJS) gần như ngừng bảo trì từ giữa 2024 | **Không dùng cho xác thực.** Giai đoạn C: một luồng thống kê để học, chạy trong docker compose |

### 3.2 Thay cho Kafka ở giai đoạn A/B: bảng outbox

Việc cần làm "bất đồng bộ" thật sự của tính năng tài khoản là **gửi email** (xác thực, đặt lại mật khẩu). Nếu gửi email ngay trong lúc xử lý request, dịch vụ email chậm hay lỗi sẽ làm việc đăng ký chậm hay lỗi theo.

Cách làm thực tế, không thêm hạ tầng mới, là **mẫu transactional outbox**:

```
Request đăng ký ──► 1 transaction Postgres: INSERT users + INSERT outbox('send_email', ...)
                                   │
Tiến trình worker (cùng image) ──► đọc outbox (FOR UPDATE SKIP LOCKED) ──► gửi email ──► đánh dấu đã xong
```

Cách này có ba ưu điểm:

- **Không mất việc:** người dùng tạo xong thì email chắc chắn được gửi, vì hai thao tác nằm trong cùng một transaction.
- **Chạy đúng khi có nhiều worker:** `SKIP LOCKED` bảo đảm hai worker không lấy trùng một việc.
- **Là cầu nối sang Kafka:** khi cần, worker chỉ việc đẩy sự kiện từ outbox sang Kafka thay vì tự gửi email. Đây đúng là cách các hệ thống thật đưa Kafka vào (mục 14).

### 3.3 Ba giai đoạn

| Giai đoạn | Tuần | Nội dung | Ra sản phẩm thật? |
|---|---|---|---|
| **A – Nền móng** | 6–8 | Postgres, Redis, Docker compose, tài khoản (Must), deploy | Có |
| **B – Hoàn thiện** | 9–10 | Xác thực email, quên mật khẩu, quản lý thiết bị, outbox + worker, đo tải, CI | Có |
| **C – Mở rộng để học** | 11 | Kubernetes trên máy (k3d), Kafka cho luồng thống kê | Không – để học và viết báo cáo |

Giai đoạn C chỉ bắt đầu khi A và B đã xong. Nếu đến tuần 10 mà B chưa xong, **cắt C**, không cắt phần bảo mật của A và B.

---

## 4. Công nghệ và cài đặt

### 4.1 Lựa chọn và lý do

| Phần | Chọn | Lý do | Phương án khác đã cân nhắc |
|---|---|---|---|
| Ngôn ngữ / runtime | Node.js LTS (≥ 22), Express 5 | Giữ nguyên như hiện tại. Express 5 tự bắt lỗi của hàm `async` | NestJS: cấu trúc chặt hơn nhưng phải học lại nhiều |
| CSDL | **PostgreSQL 17** | Chuẩn thực tế, nhiều dịch vụ quản lý sẵn, có ràng buộc và transaction đầy đủ | MySQL: tương đương. Giữ SQLite: không nhân bản được (mục 1.2) |
| Truy cập CSDL | Thư viện **`pg`** + SQL viết tay + công cụ migration tự viết (khoảng 50 dòng) | Nhóm học SQL thật; không có lớp "phép màu" che mất câu lệnh | Prisma / Drizzle: viết nhanh hơn, nhưng thêm một lớp trừu tượng phải học. Có thể đổi sau mà không ảnh hưởng API |
| Lưu session | **Redis** + `express-session` + `connect-redis` | Session dùng chung cho mọi bản sao server; đăng xuất có hiệu lực ngay lập tức | JWT: không cần nơi lưu, nhưng **không thu hồi được** trước khi hết hạn, dễ dùng sai (xem 9.1) |
| Băm mật khẩu | **scrypt** có sẵn trong `node:crypto` | Thuộc nhóm thuật toán OWASP khuyến nghị; **không cần biên dịch C++**, chạy y hệt trên Windows, Linux, Docker | argon2id (gói `argon2`): OWASP xếp hạng cao hơn, nhưng là thư viện native, có thể lỗi khi cài trên Windows. Định dạng hash có ghi tên thuật toán nên đổi sau được (mục 10.2) |
| Kiểm tra đầu vào | **zod** | Một chỗ khai báo, vừa kiểm tra vừa ra thông báo lỗi rõ ràng | Tự viết như `shared/validate.js` hiện có: đủ cho trường hợp đơn giản, không đủ cho form nhiều trường |
| Giới hạn tần suất | `express-rate-limit` + `rate-limit-redis` | Bộ đếm nằm trên Redis nên **đúng cả khi có nhiều bản sao** | Bộ đếm trong bộ nhớ: mỗi bản sao đếm riêng → kẻ tấn công thử được gấp N lần |
| Header bảo mật | `helmet` | Bật sẵn các header an toàn | – |
| Ghi log | **pino** + `pino-http` | Log dạng JSON, nhanh, có che sẵn dữ liệu nhạy cảm | `console.log`: không lọc được, không có mã request |
| Gửi email | **nodemailer**; dev dùng **Mailpit** (hộp thư giả chạy trong Docker) | Dev không gửi email thật; production chỉ cần đổi `SMTP_URL` | Gọi trực tiếp API của nhà cung cấp email: gắn chặt vào một nhà cung cấp |
| Đăng nhập Google (sau giai đoạn này) | Chỉ chọn thư viện khi có quyết định triển khai và OAuth Client ID | Tránh thêm việc khi một người đang phụ trách cả BE1 và BE2 | Google Identity Services + `google-auth-library` là phương án để đánh giá sau |
| Đo tải | **k6** | Kịch bản viết bằng JavaScript, cho số liệu p95/p99 đưa thẳng vào báo cáo | Apache JMeter: nặng, dùng giao diện |
| Container | **Docker** + **docker compose** | Mục 3 | – |
| Điều phối (giai đoạn C) | **k3d** (k3s chạy trong Docker) + Traefik có sẵn | Nhẹ, một lệnh là có cụm; Traefik hỗ trợ cả Ingress lẫn Gateway API | minikube, kind: đều được. **Không dùng ingress-nginx**: dự án đã ngừng hỗ trợ từ 3/2026 |
| Luồng sự kiện (giai đoạn C) | **Apache Kafka** (image `apache/kafka`, chế độ KRaft, 1 node) + **`@confluentinc/kafka-javascript`** | Kafka thật, không cần ZooKeeper. Thư viện được Confluent bảo trì, API giống KafkaJS | KafkaJS: dễ dùng, nhưng gần như không còn được bảo trì. Redpanda: nhẹ hơn, tương thích API Kafka |

### 4.2 Cài đặt cho từng máy

| Công cụ | Windows | Linux (Ubuntu/Debian) |
|---|---|---|
| Docker | **Docker Desktop** (bật WSL2 backend) | Docker Engine + plugin compose (`docker compose`), thêm user vào nhóm `docker` |
| Node.js LTS | Như `PLAN.md` | Như `PLAN.md` |
| k6 *(tuần 9)* | `winget install k6` | Gói `.deb` từ trang của k6 |
| k3d + kubectl *(tuần 11)* | `winget install k3d`, `winget install Kubernetes.kubectl` | Script cài đặt của k3d; kubectl theo tài liệu Kubernetes |
| Trình xem CSDL | DBeaver hoặc tiện ích PostgreSQL cho VS Code | Như Windows |

Lệnh dùng hằng ngày giống hệt nhau trên cả hai hệ: `docker compose up -d`, `npm run dev`, `npm test`.

---

## 5. Kiến trúc

### 5.1 Toàn hệ thống (giai đoạn A/B)

```
                        Trình duyệt người dùng (https://b1-soict-3-d.vercel.app)
                         │                                   │
          model .glb, JS, ảnh (CDN)                  /api/... kèm cookie sid
                         │                                   │
                ┌────────▼───────────────────────────────────▼─────────┐
                │ Vercel: phục vụ file tĩnh + chuyển tiếp /api/*  ──────┼──► (cookie là cookie cùng trang)
                └──────────────────────────────────────────────────────┘
                                                             │
                                          ┌──────────────────▼──────────────────┐
                                          │  API (Express) – 1..N bản sao,       │
                                          │  KHÔNG giữ trạng thái trong bộ nhớ   │
                                          └──────┬─────────────┬────────────────┘
                                                 │             │
                                   ┌─────────────▼──┐   ┌──────▼─────────────────────┐
                                   │ Redis          │   │ PostgreSQL                  │
                                   │ session,       │   │ users, tokens, outbox,      │
                                   │ đếm rate limit │   │ nội dung (buildings, areas…)│
                                   └────────────────┘   └──────▲─────────────────────┘
                                                               │ đọc outbox
                                                        ┌──────┴──────┐      ┌────────────┐
                                                        │ Worker      ├─────►│ SMTP       │
                                                        │ (cùng image)│      │ (Mailpit/  │
                                                        └─────────────┘      │  dịch vụ)  │
                                                                             └────────────┘
```

**Điều quan trọng nhất của sơ đồ:** server API **không giữ gì trong bộ nhớ** giữa hai request. Session nằm ở Redis, dữ liệu nằm ở Postgres, bộ đếm rate limit cũng nằm ở Redis. Vì vậy chạy 1 hay 10 bản sao sau bộ cân bằng tải đều cho kết quả như nhau. Đây là điều kiện để "nhiều người cùng lúc" giải được bằng cách **thêm bản sao**.

### 5.2 Kiến trúc trong code: modular monolith

Một ứng dụng, một lần deploy, nhưng chia module rõ ràng. Đây là cách giữ code dễ bảo trì **mà chưa phải tách microservice**. Tách sớm là sai lầm phổ biến: tốn công gấp nhiều lần, lại không đem lại lợi ích ở quy mô này.

```
routes.js      HTTP: đường dẫn, gọi zod kiểm tra đầu vào, gọi service, trả JSON
   │
service.js     NGHIỆP VỤ: quy tắc đăng ký, đăng nhập, phân quyền… không biết gì về HTTP
   │
repository.js  DỮ LIỆU: câu lệnh SQL, không có quy tắc nghiệp vụ
```

- Module mới (`auth`, `users`) có đủ 3 tầng.
- Module cũ (`buildings`, `pois`, `areas`…) giữ 2 tầng `routes` + `service`. Khi nào sửa đến thì tách thêm repository, không cần làm lại một lượt.
- Quy tắc cũ giữ nguyên: **module không import lẫn nhau**. Muốn dùng chung thì đưa xuống `infra/`, `middleware/` hoặc `shared/`.

### 5.3 Luồng đăng nhập

```
POST /api/auth/login {email, password}
 1. Kiểm tra nguồn gửi (header Origin) → rate limit theo IP và theo email (Redis)
 2. zod kiểm tra đầu vào
 3. Tìm user theo lower(email)
      không có → vẫn chạy verify với một hash giả (để thời gian trả lời như nhau) → 401 chung chung
 4. verifyPassword (scrypt, chạy trên thread pool của libuv, không chặn event loop)
      sai → ghi login_events → 401 chung chung
 5. req.session.regenerate()   ← tạo session id MỚI, chống session fixation
 6. req.session.userId, createdAt → lưu vào Redis
 7. Cập nhật last_login_at; nếu tham số hash đã cũ thì băm lại mật khẩu
 8. 200 { user } + Set-Cookie: sid=...; HttpOnly; Secure; SameSite=Lax
```

---

## 6. Cấu trúc thư mục

```
B1Web/
├── compose.yaml                     docker compose: postgres, redis, mailpit (+ api, worker, kafka theo profile)
├── deploy/
│   ├── k8s/                         (giai đoạn C) manifest cho k3d
│   │   ├── namespace.yaml  configmap.yaml  secret.example.yaml
│   │   ├── postgres.yaml   redis.yaml       ← CHỈ để học trên máy
│   │   ├── api.yaml        worker.yaml      hpa.yaml   ingress.yaml
│   │   └── README.md
│   └── k6/
│       ├── auth-smoke.js            kiểm tra nhanh sau deploy
│       └── auth-load.js             kịch bản tải (mục 11)
├── .github/workflows/
│   ├── server-ci.yml                test với Postgres + Redis thật
│   └── deploy-web.yml               (nếu dùng GitHub Pages)
├── docs/
│   ├── BACKEND_PLAN.md              file này
│   ├── API.md                       thêm phần /auth, /users
│   └── decisions/
│       ├── 004-postgres-thay-sqlite.md
│       ├── 005-session-redis-khong-jwt.md
│       └── 006-pham-vi-docker-k8s-kafka.md
├── web/
│   ├── vercel.json                  chuyển tiếp /api/* sang backend
│   └── src/
│       ├── core/ApiClient.js        thêm register/login/logout/me
│       └── features/auth/           nút đăng nhập, form, sự kiện auth:changed
└── server/
    ├── Dockerfile  .dockerignore
    ├── .env.example                 mọi biến môi trường, có chú thích
    ├── migrations/                  0001_init.sql, 0002_auth.sql … (chạy theo thứ tự, không sửa file cũ)
    ├── src/
    │   ├── index.js                 khởi động API + tắt êm khi nhận SIGTERM
    │   ├── worker.js                khởi động worker outbox
    │   ├── app.js                   gắn middleware và module
    │   ├── config.js                đọc + kiểm tra biến môi trường bằng zod (thiếu là dừng ngay)
    │   ├── infra/                   DÙNG CHUNG – kết nối ra ngoài
    │   │   ├── db.js                pool pg, hàm tx() cho transaction
    │   │   ├── redis.js             client Redis
    │   │   ├── mailer.js            nodemailer
    │   │   ├── logger.js            pino + danh sách trường cần che
    │   │   ├── migrate.js           chạy migrations/*.sql
    │   │   └── kafka.js             (giai đoạn C)
    │   ├── middleware/              DÙNG CHUNG
    │   │   ├── session.js           express-session + connect-redis + hạn tuyệt đối
    │   │   ├── requireAuth.js       401 nếu chưa đăng nhập
    │   │   ├── requireRole.js       403 nếu sai vai trò (thay requireAdmin cũ)
    │   │   ├── sameOrigin.js        kiểm tra Origin cho request ghi dữ liệu
    │   │   ├── rateLimit.js         các bộ giới hạn dùng Redis
    │   │   └── errorHandler.js     (mã request: pino-http trong app.js)
    │   ├── shared/                  DÙNG CHUNG – hàm thuần, không I/O
    │   │   ├── password.js          hashPassword / verifyPassword
    │   │   ├── tokens.js            tạo token ngẫu nhiên + băm sha256
    │   │   ├── errors.js            AppError(status, code, message)
    │   │   └── schemas.js           schema zod dùng lại (email, password)
    │   ├── modules/                 MODULE CHỨC NĂNG
    │   │   ├── auth/                routes · service · repository · schemas
    │   │   ├── users/               hồ sơ, đổi mật khẩu, xóa tài khoản
    │   │   ├── outbox/              enqueue() + bộ xử lý từng loại việc
    │   │   ├── campus/ buildings/ pois/ feedback/ stats/   (đã có)
    │   │   ├── areas/ rooms/         (theo kế hoạch tải khối, chưa có trong repo)
    │   │   └── telemetry/           (giai đoạn C) producer/consumer Kafka
    │   └── db/seed.js               nạp nội dung từ JSON (đường dẫn qua biến CONTENT_DIR)
    ├── scripts/
    │   ├── make-admin.js            npm run make-admin -- email@...
    │   └── manifest.js              (theo kế hoạch của Nam)
    └── tests/
        ├── unit/                    password, schemas, tokens – không cần CSDL
        ├── integration/             gọi API thật với Postgres + Redis từ compose
        └── fixtures/
```

---

## 7. Cơ sở dữ liệu

### 7.1 Migration

- Mỗi thay đổi lược đồ là **một file mới** trong `server/migrations/`, đặt tên tăng dần: `0001_…sql`, `0002_…sql`.
- **Không sửa** file đã merge vào `main`. Muốn đổi thì viết file mới.
- `infra/migrate.js` đọc các file theo thứ tự, ghi những file đã chạy vào bảng `schema_migrations`, và chạy mỗi file trong một transaction.
- API tự chạy migration khi khởi động (`RUN_MIGRATIONS=true`) ở môi trường dev. Ở production, migration chạy thành một bước riêng trước khi deploy, để tránh hai bản sao cùng chạy một lúc. Nếu buộc phải tự chạy, dùng `pg_advisory_lock` để chỉ một bản sao được chạy.

### 7.2 Lược đồ cho tài khoản (`0002_auth.sql`)

```sql
CREATE TABLE users (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email             text NOT NULL,
  password_hash     text,                       -- NULL dành cho tài khoản OAuth nếu bổ sung về sau
  display_name      text,
  role              text NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  email_verified_at timestamptz,
  last_login_at     timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
-- Không phân biệt hoa/thường; app cũng trim + lowercase trước khi lưu.
-- KHÔNG bỏ dấu chấm hay phần +tag của Gmail: đó vẫn là địa chỉ hợp lệ, khác người dùng có thể khác ý.
CREATE UNIQUE INDEX users_email_lower_uq ON users (lower(email));

CREATE TABLE oauth_accounts (
  provider         text NOT NULL,              -- 'google'
  provider_user_id text NOT NULL,              -- 'sub' trong ID token, KHÔNG dùng email làm khóa
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, provider_user_id)
);

CREATE TABLE auth_tokens (                     -- link xác thực email, đặt lại mật khẩu
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose     text NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
  token_hash  text NOT NULL UNIQUE,            -- sha256 của token; token gốc chỉ nằm trong email
  expires_at  timestamptz NOT NULL,
  used_at     timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX auth_tokens_user_idx ON auth_tokens (user_id, purpose);

CREATE TABLE login_events (                    -- phát hiện dò mật khẩu, hỗ trợ điều tra
  id         bigserial PRIMARY KEY,
  user_id    uuid REFERENCES users(id) ON DELETE SET NULL,
  email      text,
  success    boolean NOT NULL,
  reason     text,                             -- 'bad_password', 'unknown_email', 'rate_limited'…
  ip         inet,
  user_agent text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX login_events_created_idx ON login_events (created_at);

CREATE TABLE outbox (
  id           bigserial PRIMARY KEY,
  kind         text NOT NULL,                  -- 'send_email', sau này 'publish_event'
  payload      jsonb NOT NULL,
  attempts     int  NOT NULL DEFAULT 0,
  run_after    timestamptz NOT NULL DEFAULT now(),
  done_at      timestamptz,
  last_error   text,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX outbox_pending_idx ON outbox (run_after) WHERE done_at IS NULL;

ALTER TABLE feedback ADD COLUMN user_id uuid REFERENCES users(id) ON DELETE SET NULL;
```

Các bảng nội dung hiện có (`buildings`, `pois`, `feedback`, `visits`) đã chuyển từ `schema.sql`
sang `0001_init.sql`, đổi kiểu dữ liệu cho hợp Postgres. Các bảng của kế hoạch tải khối
(`areas`, `floors`, `rooms`, `area_links`) chưa có trong repo; khi làm sẽ thêm migration mới:

| SQLite | PostgreSQL |
|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `bigserial` |
| `TEXT` chứa JSON | `jsonb` |
| `datetime('now')` | `now()` / `timestamptz` |

### 7.3 Dọn dữ liệu định kỳ

Worker chạy mỗi giờ một lần để xóa:

- `auth_tokens` đã hết hạn quá 7 ngày;
- `outbox` đã xong quá 7 ngày;
- `login_events` cũ hơn 90 ngày.

Không giữ dữ liệu cá nhân lâu hơn mức cần thiết.

---

## 8. API

Gốc vẫn là `/api`. Định dạng lỗi **giữ tương thích** với frontend hiện tại, chỉ thêm trường `code` để frontend phân biệt loại lỗi mà không phải so sánh chuỗi thông báo:

```json
{ "error": "Email hoặc mật khẩu không đúng", "code": "INVALID_CREDENTIALS" }
```

### 8.1 Danh sách

🔐 = cần đăng nhập, 👑 = cần vai trò `admin`.

| Phương thức | Đường dẫn | Mô tả | Thành công | Lỗi chính | Mức |
|---|---|---|---|---|---|
| POST | `/auth/register` | `{ email, password, displayName? }` → tạo tài khoản và đăng nhập luôn | `201 { user }` + cookie | `400 VALIDATION`, `409 EMAIL_TAKEN`, `429` | Must |
| POST | `/auth/login` | `{ email, password }` | `200 { user }` + cookie | `401 INVALID_CREDENTIALS`, `429` | Must |
| POST | `/auth/logout` 🔐 | Xóa session hiện tại | `204` | – | Must |
| GET | `/auth/me` | Người đang đăng nhập | `200 { user }` | `401 UNAUTHENTICATED` | Must |
| POST | `/auth/verify-email` | `{ token }` | `204` | `400 TOKEN_INVALID` | Should |
| POST | `/auth/verify-email/resend` 🔐 | Gửi lại email xác thực | `202` | `429` | Should |
| POST | `/auth/password/forgot` | `{ email }`: **luôn** trả 202 dù email có tồn tại hay không | `202` | `429` | Should |
| POST | `/auth/password/reset` | `{ token, password }` → đổi mật khẩu, **xóa mọi session** của user | `204` | `400 TOKEN_INVALID` | Should |
| POST | `/auth/google` | Chưa triển khai trong giai đoạn này; xem mục 22 nếu mở rộng | – | – | Sau giai đoạn này |
| GET | `/auth/sessions` 🔐 | Các thiết bị đang đăng nhập | `200 [ … ]` | – | Should |
| DELETE | `/auth/sessions/:id` 🔐 | Đăng xuất một thiết bị | `204` | `404` | Should |
| DELETE | `/auth/sessions` 🔐 | Đăng xuất mọi thiết bị khác | `204` | – | Should |
| PATCH | `/users/me` 🔐 | `{ displayName }` | `200 { user }` | `400` | Should |
| POST | `/users/me/password` 🔐 | `{ currentPassword, newPassword }` → xóa các session khác | `204` | `401`, `400` | Should |
| DELETE | `/users/me` 🔐 | `{ password }` → xóa tài khoản | `204` | `401` | Should |
| (cũ) | `/pois`, `/areas/:id`, `GET /feedback`, `GET /stats` | Thay `requireAdmin` bằng `requireRole('admin')` | – | `401`, `403` | Must |

Đối tượng `user` trả về **không bao giờ** chứa `password_hash`:

```json
{ "id": "6f1c…", "email": "sv@gmail.com", "displayName": "Châu", "role": "user", "emailVerified": false }
```

### 8.2 Lựa chọn về email cho giai đoạn này

**(1) Báo "email đã được dùng" khi đăng ký: chọn `409 EMAIL_TAKEN` cho giai đoạn A/B.**

- *Giai đoạn A/B (đã chọn):* trả `409 EMAIL_TAKEN`. Hầu hết website thực tế đều làm vậy, và đây là cách dễ dùng nhất cho người dùng. Đổi lại, kẻ xấu biết được email nào đã có tài khoản. Rủi ro đó được giảm bằng rate limit chặt cho `/auth/register`.
- *Khi đã có email (giai đoạn B), nếu muốn chặt hơn:* luôn trả `202 "Kiểm tra hộp thư"`. Email trùng thì gửi thư "có người vừa thử đăng ký bằng email của bạn". Không lộ thông tin, nhưng người dùng phải vào hộp thư mới biết kết quả.

**(2) Không bắt xác thực email trước khi đăng nhập.** Khi luồng xác thực email giai đoạn B hoạt động, chỉ hiện nhắc nhở; các thao tác nhạy cảm như quyền admin sẽ yêu cầu email đã xác thực. Góp ý vẫn cho gửi khi chưa xác thực, theo API hiện tại. Nhờ vậy dịch vụ email có trục trặc cũng không làm người dùng bị khóa ngoài.

Ở trang đăng nhập, lỗi **luôn** là một câu chung chung: "Email hoặc mật khẩu không đúng". Không có ngoại lệ.

---

## 9. Phiên đăng nhập (session)

### 9.1 Vì sao dùng session trên Redis thay vì JWT

| | Session ID + Redis (chọn) | JWT trong cookie / localStorage |
|---|---|---|
| Đăng xuất, đổi mật khẩu, khóa tài khoản | Có hiệu lực **ngay**: xóa khóa trong Redis | JWT còn hiệu lực đến khi hết hạn, trừ khi tự xây "danh sách đen" (rốt cuộc lại cần nơi lưu) |
| Dữ liệu ở trình duyệt | Một chuỗi ngẫu nhiên, không chứa thông tin gì | Chứa thông tin người dùng (chỉ mã hóa base64, ai cũng đọc được) |
| Nhân bản server | Được, vì Redis dùng chung | Được |
| Dễ dùng sai | Ít | Nhiều: để trong localStorage thì bị đọc được nếu dính lỗi XSS; dùng sai thuật toán ký… |
| Khi nào JWT hợp lý hơn | – | Nhiều dịch vụ khác nhau cần xác thực, hoặc có app di động gọi API |

Một website một backend như dự án này: **session là lựa chọn đúng**.

### 9.2 Cấu hình

```js
// server/src/middleware/session.js
import session from 'express-session';
import { RedisStore } from 'connect-redis';   // kiểm tra cách import theo phiên bản connect-redis đang cài
import { redis } from '../infra/redis.js';
import { config } from '../config.js';

const SEVEN_DAYS = 7 * 24 * 60 * 60 * 1000;
const ABSOLUTE_MAX = 30 * 24 * 60 * 60 * 1000;

export const sessionMiddleware = session({
  name: 'sid',
  store: new RedisStore({ client: redis, prefix: 'sess:' }),
  secret: config.SESSION_SECRETS,     // mảng: phần tử đầu để ký, các phần tử sau vẫn chấp nhận → đổi khóa không làm mọi người văng ra
  resave: false,
  saveUninitialized: false,           // chưa đăng nhập thì không tạo session, không đặt cookie
  rolling: true,                      // còn dùng thì còn gia hạn (hết hạn sau 7 ngày không hoạt động)
  cookie: {
    httpOnly: true,                   // JavaScript trên trang không đọc được → giảm hại khi có XSS
    secure: config.NODE_ENV === 'production',
    sameSite: 'lax',                  // chặn gửi cookie trong request POST từ trang web khác
    maxAge: SEVEN_DAYS,
  },
});

/** Hạn tuyệt đối: dù dùng liên tục, sau 30 ngày cũng phải đăng nhập lại. */
export function absoluteTimeout(req, res, next) {
  const s = req.session;
  if (s?.userId && Date.now() - s.createdAt > ABSOLUTE_MAX) {
    return s.destroy(() => res.status(401).json({ error: 'Phiên đã hết hạn', code: 'SESSION_EXPIRED' }));
  }
  next();
}
```

Phía sau proxy (Vercel, host): phải đặt `app.set('trust proxy', config.TRUST_PROXY)`, nếu không cookie `secure` sẽ không được gửi và `req.ip` sai.

Số lớp proxy cụ thể tùy nơi deploy. Cách xác định: ghi log `req.ip` và header `x-forwarded-for` trên môi trường thật, rồi chỉnh `TRUST_PROXY` cho khớp.

### 9.3 Đăng nhập và đăng xuất trong code

```js
// modules/auth/service.js (rút gọn)
export async function establishSession(req, user) {
  await new Promise((ok, fail) => req.session.regenerate((e) => (e ? fail(e) : ok())));  // id mới
  req.session.userId = user.id;
  req.session.createdAt = Date.now();
  req.session.userAgent = req.get('user-agent')?.slice(0, 200);
  await new Promise((ok, fail) => req.session.save((e) => (e ? fail(e) : ok())));
  await redis.sAdd(`user:sessions:${user.id}`, req.sessionID);   // để liệt kê / đăng xuất các thiết bị
}
```

- **Đăng xuất:** `req.session.destroy()` + `SREM user:sessions:<uid> <sid>` + xóa cookie.
- **Đăng xuất mọi nơi** (đổi hoặc đặt lại mật khẩu): đọc tập `user:sessions:<uid>`, xóa từng khóa `sess:<sid>`, rồi xóa tập đó. Trong tập có thể còn id của session đã tự hết hạn; xóa một khóa không tồn tại cũng không sao.
- **Không lưu cả đối tượng user vào session**, chỉ lưu `userId`. Mỗi request cần thông tin user thì đọc từ Postgres, có thể cache ngắn trên Redis. Nhờ vậy đổi vai trò hay khóa tài khoản có hiệu lực ngay.

### 9.4 Cookie phải là cookie cùng trang (first-party)

Frontend chạy ở `*.vercel.app`, backend ở một tên miền khác. Nếu trình duyệt gọi thẳng sang tên miền backend, cookie trở thành **cookie bên thứ ba**, và các trình duyệt ngày càng chặn loại cookie này.

Cách làm thực tế là để **Vercel chuyển tiếp `/api/*`**. Khi đó trình duyệt chỉ nói chuyện với đúng một tên miền:

```json
// web/vercel.json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://<backend-host>/api/:path*" }
  ]
}
```

Ưu điểm của cách này:

- **Không cần CORS cho trình duyệt.**
- **Cookie `SameSite=Lax` hoạt động bình thường.**
- **Giống hệt lúc dev:** proxy của Vite cũng chuyển `/api` sang `localhost:3000` như vậy.

---

## 10. Bảo mật

### 10.1 Danh sách bắt buộc trước khi deploy

| # | Mục | Cách làm |
|---|---|---|
| 1 | Mật khẩu chỉ lưu dạng băm | scrypt, salt ngẫu nhiên cho từng mật khẩu (10.2) |
| 2 | Quy tắc mật khẩu | Tối thiểu 10, tối đa 128 ký tự; **không ép** chữ hoa hay ký tự đặc biệt (độ dài quan trọng hơn độ phức tạp); không được trùng email. Chuẩn hóa Unicode NFKC trước khi băm |
| 3 | Chống dò mật khẩu | Login: 5 lần / 15 phút cho mỗi cặp (IP, email) và 50 lần / 15 phút cho mỗi IP. Register: 5 lần / giờ cho mỗi IP. Forgot: 3 lần / giờ cho mỗi email. Bộ đếm để trên Redis |
| 4 | Không lộ thông tin qua lỗi | Lỗi đăng nhập chung chung; hash giả cho email không tồn tại; `/password/forgot` luôn trả 202 |
| 5 | Session fixation | `regenerate()` mỗi lần đăng nhập và mỗi lần đổi quyền |
| 6 | Cookie | `HttpOnly`, `Secure` (production), `SameSite=Lax`, tên `sid` (không dùng tên mặc định `connect.sid`) |
| 7 | CSRF | `SameSite=Lax` + middleware `sameOrigin` kiểm tra header `Origin` với mọi request khác GET + chỉ nhận `Content-Type: application/json` |
| 8 | Token trong email | 32 byte ngẫu nhiên; trong CSDL chỉ lưu sha256; dùng một lần; xác thực email hết hạn sau 24 giờ, đặt lại mật khẩu sau 30 phút |
| 9 | Dữ liệu nhạy cảm trong log | pino che `req.headers.cookie`, `req.headers.authorization`, `*.password`, `*.token`, `*.credential` |
| 10 | Bí mật | Chỉ để trong biến môi trường hoặc Secret của host; `.env` không bao giờ commit; `SESSION_SECRET` dài ít nhất 32 byte ngẫu nhiên |
| 11 | Header | `helmet()`; tắt `x-powered-by` |
| 12 | Giới hạn kích thước request | `express.json({ limit: '20kb' })` cho nhóm `/auth` |
| 13 | Phụ thuộc | `npm audit` trong CI; bật Dependabot của GitHub |
| 14 | Dữ liệu cá nhân | Chỉ thu email và tên hiển thị; có trang giải thích cách dùng dữ liệu; có nút xóa tài khoản. Đối chiếu với quy định hiện hành của Việt Nam về bảo vệ dữ liệu cá nhân trước khi mở cho người dùng thật |

### 10.2 Băm mật khẩu

```js
// server/src/shared/password.js
import { scrypt as scryptCb, randomBytes, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';

const scrypt = promisify(scryptCb);
// Một trong các bộ tham số scrypt OWASP liệt kê (N=2^15, r=8, p=3), cần khoảng 32 MiB RAM mỗi lần băm.
const CURRENT = { N: 2 ** 15, r: 8, p: 3 };
const MAXMEM = 64 * 1024 * 1024;
const KEYLEN = 32;

const prep = (pw) => pw.normalize('NFKC');

export async function hashPassword(pw) {
  const salt = randomBytes(16);
  const key = await scrypt(prep(pw), salt, KEYLEN, { ...CURRENT, maxmem: MAXMEM });
  // Định dạng tự mô tả → sau này đổi tham số hay đổi sang argon2 mà không phải ép mọi người đặt lại mật khẩu
  return ['scrypt', CURRENT.N, CURRENT.r, CURRENT.p, salt.toString('base64url'), key.toString('base64url')].join('$');
}

export async function verifyPassword(pw, stored) {
  const [alg, N, r, p, salt, hash] = String(stored).split('$');
  if (alg !== 'scrypt') return { ok: false, needsRehash: false };
  const expected = Buffer.from(hash, 'base64url');
  const actual = await scrypt(prep(pw), Buffer.from(salt, 'base64url'), expected.length,
    { N: Number(N), r: Number(r), p: Number(p), maxmem: MAXMEM });
  const ok = actual.length === expected.length && timingSafeEqual(actual, expected);
  const needsRehash = ok && (Number(N) !== CURRENT.N || Number(r) !== CURRENT.r || Number(p) !== CURRENT.p);
  return { ok, needsRehash };
}

// Dùng khi email không tồn tại, để thời gian phản hồi giống như khi sai mật khẩu
export const DUMMY_HASH = await hashPassword(randomBytes(16).toString('hex'));
```

Có hai lưu ý vận hành, vì phần này ảnh hưởng trực tiếp đến khả năng chịu tải:

- **scrypt cố tình chậm**, cỡ vài chục mili giây, và tốn khoảng 32 MiB RAM mỗi lần băm. Node chạy nó trên **thread pool của libuv**, mặc định chỉ có **4 luồng**. Vì vậy số lần đăng nhập mỗi giây của một bản sao bị chặn bởi thread pool này, chứ không bởi Express.
- **Hai cách tăng năng lực:** tăng `UV_THREADPOOL_SIZE` (ví dụ 8) cho khớp số CPU của container, hoặc thêm bản sao. Không nên giảm tham số băm. Số liệu cụ thể phải **đo bằng k6** (mục 11).

---

## 11. Nhiều người dùng cùng lúc: tải nằm ở đâu, đo thế nào

### 11.1 Phân tích

| Loại tải | Do ai gánh | Nhận xét |
|---|---|---|
| Model `.glb` (MB), JS, ảnh | **CDN của Vercel** | Đây là phần nặng nhất. Backend **không** phục vụ file model (đúng như kế hoạch của Nam). Đông người xem cũng không đè lên backend |
| `GET` nội dung (tòa nhà, khối, phòng) | API + Postgres | Nhẹ; có ETag. Cache được trên Redis nếu đo thấy cần |
| `GET /auth/me`, mọi request đã đăng nhập | API + 1 lần đọc Redis + 1 lần đọc Postgres | Rất nhẹ; tăng tuyến tính theo số bản sao |
| Đăng nhập / đăng ký | **CPU (scrypt)** | Chỗ tốn nhất của backend, nhưng hiếm (mỗi người vài lần mỗi tuần) |
| Kết nối Postgres | Pool của `pg` | **Giới hạn thật thường nằm ở đây**: tổng kết nối = số bản sao × kích thước pool. Gói miễn phí thường giới hạn số kết nối. Đặt `PG_POOL_MAX` nhỏ (5–10) và ghi trong `.env.example` |
| Ghi đồng thời | Postgres | Đăng ký cùng một email cùng lúc → ràng buộc `UNIQUE` chặn, bắt lỗi `23505` thành `409`. Đếm lượt xem → `INSERT … ON CONFLICT DO UPDATE` (nguyên tử) |

Kết luận thực tế:

- Một bản sao Node.js nhỏ phục vụ được **hàng trăm request JSON đơn giản mỗi giây**. Con số chính xác phụ thuộc máy, nên phải đo.
- Một buổi demo cả lớp vài trăm người là trong tầm.
- Muốn hơn nữa thì **thêm bản sao**: kiến trúc stateless ở mục 5 cho phép làm vậy ngay mà không phải sửa code.

### 11.2 Đo tải bằng k6

```js
// deploy/k6/auth-load.js – chạy: k6 run -e BASE=http://localhost:3000 deploy/k6/auth-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 200 },     // 200 người dùng ảo cùng lúc
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'http_req_duration{name:me}': ['p(95)<200'],
    'http_req_duration{name:login}': ['p(95)<800'],
  },
};

const headers = { 'Content-Type': 'application/json', Origin: __ENV.ORIGIN || 'http://localhost:5173' };

export default function () {
  const email = `load+${__VU}@example.test`;   // tài khoản tạo sẵn bằng script seed riêng cho test tải
  const res = http.post(`${__ENV.BASE}/api/auth/login`,
    JSON.stringify({ email, password: 'mat-khau-test-tai-01' }), { headers, tags: { name: 'login' } });
  check(res, { 'login 200': (r) => r.status === 200 });
  for (let i = 0; i < 10; i++) {               // người thật: đăng nhập 1 lần, dùng nhiều lần
    check(http.get(`${__ENV.BASE}/api/auth/me`, { headers, tags: { name: 'me' } }), { 'me 200': (r) => r.status === 200 });
    sleep(1);
  }
}
```

Chạy 3 lần cho báo cáo:

1. 1 bản sao;
2. 2 bản sao sau bộ cân bằng tải (docker compose `--scale api=2` + Traefik, hoặc k3d ở giai đoạn C);
3. 2 bản sao với `UV_THREADPOOL_SIZE=8`.

Ghi bảng gồm p95, p99, số request mỗi giây và tỉ lệ lỗi. Đây là **bằng chứng bằng số** cho câu "hệ thống phục vụ được nhiều người cùng lúc".

**Không chạy k6 vào bản production** trên gói miễn phí: có thể hết hạn mức hoặc bị khóa dịch vụ. Chỉ chạy trên máy hoặc trên môi trường thử riêng.

---

## 12. Docker và docker compose

### 12.1 Hai cách làm việc hằng ngày

| Cách | Lệnh | Khi nào dùng |
|---|---|---|
| **Hạ tầng trong Docker, code chạy trên máy** (mặc định) | `docker compose up -d` rồi `cd server && npm run dev` | Viết code hằng ngày: tự tải lại khi sửa, gỡ lỗi dễ |
| **Tất cả trong Docker** | `docker compose --profile full up --build` | Kiểm tra image trước khi deploy; người làm frontend chỉ cần chạy backend lên mà không cài Node cho server |

### 12.2 `compose.yaml` (đặt ở gốc repo)

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_USER: tour
      POSTGRES_PASSWORD: tour          # chỉ dùng cho dev
      POSTGRES_DB: tour
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tour -d tour"]
      interval: 5s
      timeout: 3s
      retries: 20

  redis:
    image: redis:7
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20

  mailpit:                              # hộp thư giả: xem email đã gửi tại http://localhost:8025
    image: axllent/mailpit
    ports: ["8025:8025", "1025:1025"]

  api:
    profiles: ["full"]
    build: { context: ., dockerfile: server/Dockerfile }
    env_file: server/.env.docker
    ports: ["3000:3000"]
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }

  worker:
    profiles: ["full"]
    build: { context: ., dockerfile: server/Dockerfile }
    command: ["node", "src/worker.js"]
    env_file: server/.env.docker
    depends_on:
      postgres: { condition: service_healthy }

volumes:
  pgdata: {}
```

- Xóa sạch dữ liệu dev để làm lại từ đầu: `docker compose down -v`.
- Đổi phiên bản lớn của Postgres sau này (ví dụ 17 → 18) **không** làm được chỉ bằng cách đổi tag image. Dữ liệu cũ phải được xuất ra rồi nhập lại. Với dev thì cứ `down -v` cho nhanh.

### 12.3 `server/Dockerfile`

Build context là **gốc repo**, để image có thể lấy kèm dữ liệu nội dung trong `web/public/data`.

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY server/package.json server/package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-bookworm-slim
ENV NODE_ENV=production \
    CONTENT_DIR=/app/content
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY server/package.json ./
COPY server/src ./src
COPY server/migrations ./migrations
COPY web/public/data ./content
USER node
EXPOSE 3000
CMD ["node", "src/index.js"]
```

`server/.dockerignore` (cùng với `.dockerignore` ở gốc repo) loại `node_modules`, `.env*`, `tests`, `data/*.db`, `blender/`, `web/public/models/`. Nhờ vậy image nhỏ và không lọt bí mật vào image.

### 12.4 Tắt êm và kiểm tra sức khỏe

Hai việc này bắt buộc nếu muốn nhân bản và cập nhật không gián đoạn, dù deploy trên host đơn giản hay trên Kubernetes.

```js
// server/src/index.js (phần cuối)
const server = app.listen(config.PORT, () => logger.info({ port: config.PORT }, 'API đã chạy'));

async function shutdown(signal) {
  logger.info({ signal }, 'Đang tắt: ngừng nhận request mới, chờ request đang chạy xong');
  server.close(async () => {
    await Promise.allSettled([pool.end(), redis.quit()]);
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 10_000).unref();   // quá 10 giây thì tắt cứng
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
```

| Đường dẫn | Kiểm tra | Dùng cho |
|---|---|---|
| `GET /healthz` | Tiến trình còn sống (không gọi CSDL) | *liveness*: chết thì khởi động lại |
| `GET /readyz` | `SELECT 1` tới Postgres + `PING` tới Redis | *readiness*: chưa sẵn sàng thì chưa đưa request vào |

`/healthz` **không được** phụ thuộc Postgres. Nếu phụ thuộc, khi Postgres trục trặc, mọi bản sao sẽ bị khởi động lại liên tục và làm sự cố nặng thêm.

### 12.5 Biến môi trường (`server/.env.example`)

```bash
NODE_ENV=development
PORT=3000
DATABASE_URL=postgres://tour:tour@localhost:5432/tour
PG_POOL_MAX=10
REDIS_URL=redis://localhost:6379
SESSION_SECRETS=thay-bang-chuoi-ngau-nhien-dai-it-nhat-32-byte   # nhiều khóa: ngăn cách bởi dấu phẩy
TRUST_PROXY=1
APP_ORIGINS=http://localhost:5173                                # các Origin được phép gửi request ghi
APP_URL=http://localhost:5173                                    # dùng để tạo link trong email
SMTP_URL=smtp://localhost:1025
MAIL_FROM="B1Web <no-reply@example.test>"
# GOOGLE_CLIENT_ID chỉ thêm khi quyết định làm đăng nhập Google sau giai đoạn này.
RUN_MIGRATIONS=true
CONTENT_DIR=../web/public/data
LOG_LEVEL=info
UV_THREADPOOL_SIZE=4
```

`config.js` kiểm tra mọi biến bằng zod khi khởi động. Thiếu hoặc sai biến nào thì **dừng ngay với thông báo rõ ràng**, không chạy với cấu hình nửa vời.

---

## 13. Kubernetes (giai đoạn C – học trên máy)

### 13.1 Mục tiêu học

Chạy đúng image đã dùng với docker compose trên một cụm k3d, rồi tự tay **thấy** năm việc Kubernetes làm:

1. Xóa một pod → nó tự được tạo lại.
2. Scale từ 2 lên 4 bản sao bằng một lệnh.
3. Cập nhật image mà không gián đoạn: rolling update, chờ `/readyz` báo sẵn sàng mới chuyển request sang pod mới.
4. HPA tự tăng số bản sao khi chạy k6.
5. Secret và ConfigMap tách cấu hình khỏi image.

### 13.2 Các bước

```bash
k3d cluster create b1 --agents 1 -p "8080:80@loadbalancer"
docker build -t b1-api:dev -f server/Dockerfile .
k3d image import b1-api:dev -c b1
kubectl apply -f deploy/k8s/namespace.yaml
kubectl -n b1 create secret generic api-secrets --from-env-file=server/.env.k8s   # không commit file này
kubectl apply -f deploy/k8s/
kubectl -n b1 get pods -w
# Mở http://localhost:8080/api/readyz
```

### 13.3 Phần chính của `deploy/k8s/api.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: api, namespace: b1 }
spec:
  replicas: 2
  selector: { matchLabels: { app: api } }
  strategy: { rollingUpdate: { maxUnavailable: 0, maxSurge: 1 } }
  template:
    metadata: { labels: { app: api } }
    spec:
      terminationGracePeriodSeconds: 20
      containers:
        - name: api
          image: b1-api:dev
          imagePullPolicy: IfNotPresent
          ports: [{ containerPort: 3000 }]
          envFrom:
            - configMapRef: { name: api-config }
            - secretRef: { name: api-secrets }
          readinessProbe: { httpGet: { path: /readyz, port: 3000 }, periodSeconds: 5 }
          livenessProbe:  { httpGet: { path: /healthz, port: 3000 }, periodSeconds: 10, failureThreshold: 3 }
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits:   { cpu: 500m, memory: 384Mi }   # đủ cho vài lần băm scrypt song song (≈32 MiB/lần)
---
apiVersion: v1
kind: Service
metadata: { name: api, namespace: b1 }
spec:
  selector: { app: api }
  ports: [{ port: 80, targetPort: 3000 }]
```

`ingress.yaml` dùng tài nguyên `Ingress` chuẩn, với controller **Traefik có sẵn trong k3d**.

**Không cài ingress-nginx**: dự án đã ngừng hỗ trợ từ tháng 3/2026. Muốn học thêm thì chuyển sang **Gateway API** (Traefik cũng hỗ trợ). Đây là hướng cộng đồng Kubernetes khuyến nghị.

`postgres.yaml` và `redis.yaml` (StatefulSet với image chính thức) **chỉ dùng để học trên máy**. Chạy CSDL trong Kubernetes ở môi trường thật là việc khó: sao lưu, nâng cấp, khôi phục. Thực tế, hầu hết các nhóm dùng dịch vụ CSDL được quản lý sẵn.

### 13.4 Vì sao không đưa Kubernetes lên production ở dự án này

- **Chi phí:** cụm Kubernetes trên cloud tốn tiền liên tục; gói miễn phí hạn chế và hay thay đổi.
- **Vận hành:** cần người theo dõi cập nhật cụm, chứng chỉ TLS, controller, tài nguyên.
- **Không cần thiết:** host kiểu Render/Railway/Fly đã tự khởi động lại, nhân bản và triển khai không gián đoạn từ chính Dockerfile này.

Vì image và cách cấu hình theo biến môi trường giống hệt nhau, khi nào cần, việc chuyển lên Kubernetes thật **không phải sửa code**. Đó là giá trị thật của việc học ở giai đoạn C.

---

## 14. Kafka (giai đoạn C – một luồng thống kê)

### 14.1 Bài toán chọn để học

Kế hoạch của Nam có `POST /stats/area-load`: trình duyệt gửi thời gian tải từng khối. Đây là **dữ liệu sự kiện** có ba đặc điểm hợp với Kafka:

- Mất vài bản ghi cũng không sao.
- Có thể có nhiều bên muốn đọc: tính thống kê, phát hiện khối tải chậm, lưu trữ lâu dài.
- Có lúc dồn dập, khi cả lớp mở trang cùng lúc.

```
Trình duyệt ── POST /stats/area-load ──► API ── produce ──► topic telemetry.area-load.v1
                                         (trả 204 ngay)            │
                                                                   ├─► consumer "stats-aggregator" → bảng area_load_daily (Postgres)
                                                                   └─► (sau này) consumer khác, không phải sửa API
```

### 14.2 Quy ước

- **Tên topic có phiên bản:** `<miền>.<sự-kiện>.v1`. Đổi cấu trúc thông điệp mà không tương thích ngược thì tạo `v2`.
- **Thông điệp dạng JSON** có `eventId` (uuid), `occurredAt`, `schemaVersion`.
- **Consumer phải chịu được việc nhận trùng.** Kafka đảm bảo "ít nhất một lần", nên ghi vào Postgres theo `eventId` với `ON CONFLICT DO NOTHING`.
- **Khóa của thông điệp** là `areaId`, để sự kiện cùng một khối vào cùng một partition và giữ đúng thứ tự.
- **Không có Kafka thì API vẫn chạy:** gửi thất bại chỉ ghi log rồi bỏ qua. Thống kê không được làm hỏng trải nghiệm tham quan.

### 14.3 Chạy trong docker compose

Thêm service vào `compose.yaml` với `profiles: ["kafka"]`, dùng image `apache/kafka` ở chế độ KRaft một node, mở 2 listener: một cho container trong mạng compose, một cho máy chủ `localhost:9092`.

Các biến cấu hình listener (`KAFKA_LISTENERS`, `KAFKA_ADVERTISED_LISTENERS`, `KAFKA_CONTROLLER_QUORUM_VOTERS`…) phải **viết theo tài liệu của đúng phiên bản image** đang dùng. Đây là chỗ hay cấu hình sai nhất khi mới làm.

Thư viện: `@confluentinc/kafka-javascript`, dùng phần API kiểu KafkaJS (`kafka.producer()`, `kafka.consumer({ groupId })`). Đây là thư viện native có bản dựng sẵn; trước khi chọn, kiểm tra đã có bản cho phiên bản Node và hệ điều hành của nhóm chưa.

### 14.4 Kết nối với outbox

Bước "thật" tiếp theo, nếu còn thời gian: thay vì API gửi trực tiếp, worker **đẩy sự kiện `user.registered.v1` từ bảng outbox sang Kafka**. Từ đó, gửi email chào mừng hay cập nhật thống kê trở thành các consumer riêng.

Đây là cách các hệ thống thật đưa Kafka vào: **dần dần, từ chỗ đã có outbox**, không phải viết lại từ đầu.

---

## 15. Kiểm thử và CI

### 15.1 Test tối thiểu phải có

| Nhóm | Test |
|---|---|
| Đơn vị | `hashPassword` → `verifyPassword` đúng; sai mật khẩu → `ok:false`; tham số cũ → `needsRehash:true`; hash lạ → không ném lỗi |
| Đăng ký | Thành công → 201, có cookie `sid` `HttpOnly`; email sai dạng / mật khẩu ngắn → 400; email trùng (khác hoa/thường) → 409; **hai request đăng ký cùng email chạy song song → đúng một cái thành công** |
| Đăng nhập | Đúng → 200 + session id **khác** session id trước đó; sai mật khẩu và email không tồn tại → cùng 401, cùng thông báo; lần thử thứ 6 → 429 |
| Phiên | `/me` có cookie → 200; sau logout → 401; sau đổi mật khẩu → session ở "thiết bị khác" → 401; session quá hạn tuyệt đối → 401 |
| Phân quyền | `/pois` không đăng nhập → 401; user thường → 403; admin → được |
| CSRF | POST với `Origin` lạ → 403; không có `Content-Type: application/json` → 415 |
| Token email | Dùng 2 lần → lần 2 bị 400; hết hạn → 400 |
| Outbox | Hai worker cùng chạy → mỗi email chỉ gửi một lần (kiểm tra qua API của Mailpit) |

Test tích hợp chạy với Postgres và Redis thật từ docker compose. Giữa các test, xóa sạch dữ liệu bằng `TRUNCATE … RESTART IDENTITY CASCADE` và `FLUSHDB` (Redis số 1, dành riêng cho test).

### 15.2 GitHub Actions (`.github/workflows/server-ci.yml`)

```yaml
name: server-ci
on:
  pull_request:
    paths: ["server/**", ".github/workflows/server-ci.yml"]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env: { POSTGRES_USER: tour, POSTGRES_PASSWORD: tour, POSTGRES_DB: tour_test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U tour" --health-interval 5s --health-timeout 3s --health-retries 20
      redis:
        image: redis:7
        ports: ["6379:6379"]
    env:
      DATABASE_URL: postgres://tour:tour@localhost:5432/tour_test
      REDIS_URL: redis://localhost:6379/1
      SESSION_SECRETS: ci-only-secret-ci-only-secret-0001
      APP_ORIGINS: http://localhost:5173
      NODE_ENV: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm, cache-dependency-path: server/package-lock.json }
      - run: npm ci
        working-directory: server
      - run: npm test
        working-directory: server
      - run: npm audit --omit=dev --audit-level=high
        working-directory: server
      - run: docker build -f server/Dockerfile -t b1-api:ci .    # đảm bảo image build được
```

---

## 16. Triển khai (deploy)

| Thành phần | Gợi ý | Lưu ý |
|---|---|---|
| Frontend | Vercel (đang dùng) | Thêm `web/vercel.json` chuyển tiếp `/api/*` (9.4) |
| API + worker | Host chạy được Docker image: Render, Railway, Fly.io… | Deploy **từ `server/Dockerfile`**. Đặt mọi biến ở mục 12.5 trong phần Secrets của host. Bật health check `/readyz` |
| PostgreSQL | Dịch vụ quản lý sẵn có gói miễn phí (ví dụ Neon, Supabase) | Dùng chuỗi kết nối có `sslmode=require`. Để ý giới hạn số kết nối → `PG_POOL_MAX` |
| Redis | Dịch vụ quản lý sẵn (ví dụ Upstash) | Thường dùng `rediss://` (có TLS). Gói miễn phí giới hạn **theo số lệnh**: session gia hạn mỗi request (`rolling`) tốn một lệnh ghi mỗi lần, cần theo dõi |
| Email | Production cần dịch vụ SMTP thật | SMTP của Gmail với *App Password* dùng được cho demo, nhưng giới hạn số thư/ngày và dễ vào hộp spam. Dịch vụ gửi thư giao dịch cho kết quả ổn định hơn |
| Migration | Chạy `npm run migrate` thành **một bước riêng** trước khi bản mới nhận request | Nếu host không có bước "pre-deploy" thì dùng `pg_advisory_lock` trong `migrate.js` |

**Điều kiện gói miễn phí của các dịch vụ trên hay thay đổi.** Kiểm tra lại lúc deploy và ghi lựa chọn cuối cùng vào `docs/decisions/007-noi-deploy-backend.md`.

**Hai môi trường:**

- **Preview:** mỗi Pull Request có bản Vercel Preview, trỏ tới backend *staging*, với CSDL riêng hoặc schema riêng.
- **Production:** chỉ deploy từ `main`.

**Không dùng chung CSDL** giữa preview và production. Một lần test lỗi có thể xóa tài khoản người dùng thật.

---

## 17. Thay đổi ở frontend

Phần này do người làm frontend phụ trách, phối hợp với backend.

- `ApiClient` thêm `register()`, `login()`, `logout()`, `me()`, và gửi kèm header `Content-Type: application/json` cho mọi request ghi.
  - Vì gọi cùng tên miền (nhờ proxy), cookie tự được gửi, không cần cấu hình CORS.
  - Không có backend thì **ẩn nút đăng nhập**. Không có dữ liệu tĩnh dự phòng cho tài khoản.
- `features/auth/`:
  - nút "Đăng nhập" trên toolbar;
  - panel form đăng nhập / đăng ký, dùng `createPanel()`;
  - phát sự kiện `auth:changed` (giá trị `user` hoặc `null`) lên EventBus.
- Khi mở trang: gọi `GET /api/auth/me` một lần để biết đã đăng nhập chưa.
- **Không lưu gì về đăng nhập trong `localStorage`.** Cookie `HttpOnly` lo toàn bộ.
- Trang quản trị: bỏ ô nhập `ADMIN_TOKEN`, thay bằng đăng nhập tài khoản có vai trò `admin`.

**Chuyển đổi quyền quản trị an toàn:**

- **Tuần 7:** backend chấp nhận **cả hai** cách, token cũ hoặc session admin.
- **Tuần 8:** trang quản trị đã chuyển xong → xóa `ADMIN_TOKEN` khỏi code và khỏi biến môi trường.
- BE1 (người làm chức năng admin) giữ quyền tạo admin đầu tiên bằng `npm run make-admin -- email@...`. Không có API nào tự nâng quyền.

---

## 18. Phân công

Phần này dựa trên cách chia BE1/BE2 trong kế hoạch của Nam, để không chồng chéo file:

| Người | Phụ trách trong kế hoạch này | Thư mục | Phối hợp |
|---|---|---|---|
| **BE1** (CSDL + API) | Chuyển Postgres + migration; module `auth`, `users`; session; phân quyền; test tích hợp | `server/src/modules/auth`, `users`, `middleware/`, `migrations/` | Frontend auth (TV4), quản trị |
| **BE2** (script + hạ tầng) | Docker, compose, Dockerfile, CI; outbox + worker + email; k6; deploy; giai đoạn C (k3d, Kafka) | `compose.yaml`, `server/Dockerfile`, `infra/`, `modules/outbox`, `deploy/`, `.github/` | TV1 (deploy frontend, `vercel.json`) |
| **TV4** (frontend giao diện) | `features/auth`, sửa trang quản trị | `web/src/features/auth`, `web/admin` | BE1 |
| **TV1** (frontend lõi) | `ApiClient`, `vercel.json`, review bảo mật phía frontend | `web/src/core`, `web/vercel.json` | BE2 |

**Đánh giá khối lượng thẳng thắn.** Ước tính theo ngày công của một sinh viên:

| Việc | Ngày công |
|---|---|
| Chuyển Postgres + công cụ migration + sửa test cũ | 3 |
| Docker compose + Dockerfile | 1–2 |
| Đăng ký / đăng nhập / session / phân quyền (Must) | 5–6 |
| Rate limit + các mục bảo mật | 2 |
| Outbox + worker + xác thực email + quên mật khẩu | 4 |
| Quản lý thiết bị, đổi mật khẩu, xóa tài khoản | 2 |
| Deploy backend + Postgres + Redis + `vercel.json` | 2 |
| CI | 1 |
| k6 + báo cáo số liệu | 2 |
| **Tổng Must + Should** | **khoảng 22–24** |
| Kubernetes trên k3d | 4–5 |
| Kafka luồng thống kê | 4–5 |

Người làm nhánh `dtm` kiêm cả BE1 và BE2, đồng thời còn kế hoạch tải khối của Nam (manifest, areas, rooms, đến 6/12). Khối lượng này phải ưu tiên Must và cắt giai đoạn C trước nếu thiếu thời gian.

Thứ tự ưu tiên đã chọn cho nhánh `dtm` khi thiếu thời gian:

1. Mốc 6/12 của kế hoạch tải khối.
2. Must của tài khoản.
3. Should của tài khoản.
4. Giai đoạn C.

Người phụ trách `dtm` làm cả BE1 và BE2; không đánh đổi mốc tải khối hoặc bảo mật Must để thêm việc giai đoạn C.

---

## 19. Lộ trình theo tuần

Tuần 1 = 12/10/2026, khớp với kế hoạch của Nam.

### Tuần 6 (16–22/11) – Chốt và dựng nền

- [x] Người phụ trách `dtm`: chốt quyết định ở mục 24; ADR 004, 005, 006 đã được ghi trong `docs/decisions/`.
- [ ] Cả nhóm: duyệt các quyết định này theo quy trình PR.
- [x] BE2: `compose.yaml` (Postgres, Redis, Mailpit) chạy healthy trên máy local của người phụ trách `dtm`.
- [ ] Cả nhóm: xác nhận mỗi thành viên chạy được `docker compose up -d` trên máy mình.
- [x] BE1: `infra/db.js`, `infra/migrate.js`, `0001_init.sql` (chuyển bảng cũ); sửa `seed.js` và các service cũ sang `pg` (dạng async); **6 test cũ pass trên Postgres**.
- [x] BE1: ghi hợp đồng `/auth` trong `docs/API.md` theo quyết định tuần 6.
- [ ] TV4: xem và xác nhận hợp đồng `/auth` để frontend triển khai đúng.

Mốc: dự án chạy trên Postgres; API cũ không đổi hình dạng (frontend không phải sửa gì).

**Trạng thái nhánh `dtm` ngày 18/11/2026:** phần BE1 ở trên đã có trong patch giai đoạn A;
test hiện tại gồm 7 bài kiểm tra API nội dung và 23 bài khác, tổng cộng 30/30 pass trên Postgres/Redis local.
`docker compose up -d --wait` đưa Postgres, Redis, Mailpit vào trạng thái healthy; `/readyz`,
`/api/campus`, `/api/buildings/b1` trả 200. ADR 004–006 và hợp đồng `/auth` đã có trong repo.
Chưa xác nhận mọi thành viên chạy Compose được, nhóm đã duyệt ADR/ưu tiên và TV4 đã thống nhất
hợp đồng `/auth`; các mục cần phối hợp đó vẫn để mở ở checklist.

Mốc 22/11 của kế hoạch tải khối vẫn giữ. Phần `areas`/`rooms` viết thẳng trên Postgres, nhờ vậy không phải chuyển đổi hai lần.
Kế hoạch tải khối chi tiết của Nam chưa có trong workspace này; hiện chưa có module `areas`, `rooms`
hoặc script `manifest`. Đây là mốc riêng còn cần đặc tả để triển khai, không thuộc phần nền PostgreSQL
đã kiểm chứng ở trên.

### Tuần 7 (23–29/11) – Tài khoản (Must)

- [ ] BE1: `0002_auth.sql`; `shared/password.js`; session + Redis; `register`, `login`, `logout`, `me`; `requireAuth`, `requireRole`; giai đoạn chấp nhận cả token cũ và session admin.
- [ ] BE1: test mục 15.1 cho đăng ký, đăng nhập, phiên, phân quyền.
- [ ] BE2: rate limit trên Redis; `sameOrigin`; `helmet`; pino che dữ liệu nhạy cảm; `/healthz`, `/readyz`; tắt êm.
- [ ] TV4: form đăng nhập/đăng ký chạy với backend trên máy (qua proxy Vite).

### Tuần 8 (30/11–6/12) – Deploy giai đoạn A

- [ ] BE2: Dockerfile; deploy API + Postgres + Redis; `web/vercel.json`; Preview dùng backend staging.
- [ ] TV4 + BE1: trang quản trị dùng tài khoản admin; **xóa `ADMIN_TOKEN`**.
- [ ] BE2: CI (mục 15.2) bắt buộc pass trước khi merge.

Mốc: trên link Vercel, đăng ký → đóng trình duyệt → mở lại vẫn đăng nhập; tài khoản admin quản lý được POI. Trùng ngày với mốc 6/12 của kế hoạch tải khối → **không nhận thêm việc mới tuần này**.

### Tuần 9 (7–13/12) – Giai đoạn B, phần 1

- [ ] BE2: bảng outbox + `worker.js` + `nodemailer`; email hiện trong Mailpit.
- [ ] BE1: xác thực email; quên / đặt lại mật khẩu (xóa mọi session); đổi mật khẩu.
- [ ] BE2: k6 chạy trên máy, lần đo đầu tiên.

### Tuần 10 (14–20/12) – Giai đoạn B, phần 2

- [ ] BE1: danh sách thiết bị và đăng xuất từ xa; xóa tài khoản. Đăng nhập Google để sau giai đoạn này.
- [ ] BE2: k6 với 1 và 2 bản sao; bảng số liệu cho báo cáo; dọn dữ liệu định kỳ.
- [ ] Cả nhóm: rà lại danh sách bảo mật ở mục 10.1, từng dòng một, có người thứ hai kiểm tra chéo.

Mốc: đủ Must + Should. **Nếu chưa đạt thì bỏ tuần 11, dùng để hoàn thiện.**

### Tuần 11 (21–27/12) – Giai đoạn C (Could)

- [ ] BE2: k3d, các manifest, thử 5 việc ở mục 13.1, chụp lại kết quả.
- [ ] BE1: Kafka luồng `telemetry.area-load.v1` + consumer tổng hợp.

### Tuần 12 (28/12–3/1) – Đệm

Không thêm tính năng. Chỉ sửa lỗi, viết báo cáo, tổng duyệt demo.

---

## 20. Quy tắc làm việc

Giữ nguyên `docs/CONVENTIONS.md` (nhánh, PR, review) và bổ sung các quy tắc sau:

1. **Đổi API → sửa `docs/API.md` trước**, trong cùng PR, có người frontend duyệt.
2. **Đổi lược đồ → file migration mới.** Không bao giờ sửa file migration đã merge.
3. **PR đụng tới `modules/auth`, `middleware/session.js`, `shared/password.js`** phải có **2 người duyệt**, trong đó một người không phải tác giả của module.
4. **Không có bí mật trong Git.** Lỡ commit thì **đổi ngay** bí mật đó; xóa khỏi lịch sử Git là chưa đủ.
5. **Thêm thư viện** phải ghi lý do trong mô tả PR: thư viện còn được bảo trì không, có cần biên dịch native không, có chạy trên Windows không.
6. **Mọi biến môi trường mới** phải có trong `.env.example` kèm chú thích, và được kiểm tra trong `config.js`.

---

## 21. Rủi ro

| Rủi ro | Dấu hiệu | Phòng / xử lý |
|---|---|---|
| Ôm đồm: Kubernetes, Kafka ăn hết thời gian của phần chính | Tuần 10 chưa xong Should | Giai đoạn C chỉ bắt đầu khi B xong; cắt C trước, không cắt bảo mật |
| Chồng việc với kế hoạch tải khối | Mốc 6/12 trễ | Thứ tự ưu tiên ở mục 18; tuần 8 không nhận việc mới |
| Cookie không được gửi ở bản deploy | Đăng nhập xong `/me` vẫn trả 401 | Dùng proxy `vercel.json`; đặt đúng `trust proxy`; kiểm tra cờ `Secure` |
| Lộ bí mật (`SESSION_SECRETS`, chuỗi kết nối CSDL) | Bí mật xuất hiện trong commit hay log | `.gitignore`, pino che dữ liệu, bật *secret scanning* của GitHub; lộ thì đổi ngay |
| Bị dò mật khẩu | `login_events` tăng vọt các lần thất bại | Rate limit trên Redis; theo dõi `login_events` |
| Hết kết nối Postgres | Lỗi `too many connections` khi tăng bản sao | `PG_POOL_MAX` nhỏ; tính tổng số bản sao × pool trước khi scale |
| Hết hạn mức Redis gói miễn phí | Redis từ chối lệnh, đăng nhập lỗi hàng loạt | Theo dõi số lệnh; cân nhắc tắt `rolling` hoặc chỉ gia hạn khi gần hết hạn |
| Email vào spam / không gửi được | Người dùng không nhận được link | Không chặn đăng nhập khi chưa xác thực (8.2); có nút gửi lại; dùng dịch vụ gửi thư đúng chuẩn |
| Thư viện native lỗi cài trên Windows | `npm install` báo lỗi build | Ưu tiên thư viện thuần JS hoặc có sẵn trong Node (scrypt); chạy trong Docker |
| Migration chạy hai lần cùng lúc | Lỗi bảng đã tồn tại khi deploy nhiều bản sao | Bước migrate riêng hoặc `pg_advisory_lock` |
| Dữ liệu test lẫn dữ liệu thật | Mất tài khoản người dùng thật | CSDL riêng cho staging và production; k6 không chạy vào production |
| Cấu hình Kafka sai listener | Consumer không kết nối được | Theo đúng tài liệu image; Kafka lỗi thì API vẫn chạy (14.2) |

---

## 22. Mở rộng về sau

| Khi xuất hiện nhu cầu | Thì làm |
|---|---|
| Cần đăng nhập bằng Google sau giai đoạn này | Tạo OAuth Client ID cho tên miền triển khai; đánh giá Google Identity Services + `google-auth-library`, rồi mới thêm API và giao diện |
| Có app di động hoặc dịch vụ khác cần xác thực | Thêm OAuth 2.0 / OpenID Connect, hoặc token truy cập ngắn hạn cho API; website vẫn dùng session |
| Cần an toàn hơn cho admin | 2FA bằng TOTP, rồi passkey (WebAuthn) |
| Nhiều vai trò (giảng viên, quản lý từng tòa) | Bảng `roles` + `user_roles` + quyền theo tài nguyên, thay cột `role` |
| Truy cập tăng mạnh | Thêm bản sao API; cache nội dung trên Redis; Postgres có bản sao chỉ đọc |
| Nhiều luồng sự kiện, nhiều bên tiêu thụ | Mở rộng Kafka từ outbox (14.4); quản lý lược đồ thông điệp bằng Schema Registry |
| Một phần hệ thống cần scale hoặc deploy riêng | Lúc đó mới tách module đó thành dịch vụ riêng. Nhờ ranh giới module đã rõ, việc tách nhẹ hơn nhiều |
| Cần theo dõi chuyên nghiệp | OpenTelemetry (trace), Prometheus + Grafana (số liệu), cảnh báo khi lỗi tăng |

---

## 23. Tài liệu học

| Chủ đề | Tài liệu |
|---|---|
| Xác thực, mật khẩu, session | OWASP Cheat Sheet Series – *Authentication*, *Password Storage*, *Session Management*, *Cross-Site Request Forgery Prevention*, *Forgot Password* |
| Express | expressjs.com – *Production best practices: security*, *Health checks and graceful shutdown* |
| Node.js | Tài liệu `node:crypto` (`scrypt`, `timingSafeEqual`), *Don't block the event loop* |
| PostgreSQL | Tài liệu chính thức – *Tutorial*, *Constraints*, *Transaction Isolation*, `SELECT … FOR UPDATE SKIP LOCKED` |
| Redis | redis.io – *Data types* (string, set), *Expiration* |
| Docker | Tài liệu Docker – *Get started*, *Compose file reference*, *Multi-stage builds* |
| Kubernetes | kubernetes.io – *Tutorials: Kubernetes Basics*; tài liệu k3d; *Gateway API* |
| Kafka | Apache Kafka *Quickstart*; tài liệu `confluent-kafka-javascript`; mẫu *Transactional Outbox* (microservices.io) |
| Đo tải | Tài liệu k6 – *Running k6*, *Thresholds* |
| Kiến trúc | "The Twelve-Factor App" (12factor.net) – cấu hình qua biến môi trường, tiến trình không giữ trạng thái |

---

## 24. Việc cần chốt ngay tuần này

- [x] **Thứ tự ưu tiên** giữa kế hoạch tải khối và kế hoạch này (mục 18): mốc tải khối → Must → Should → giai đoạn C.
- [x] **ADR 004 – Postgres thay SQLite.** Thay `docs/decisions/002`; ghi rõ vì sao bỏ câu "không thêm thư viện mới" trong kế hoạch tải khối.
- [x] **ADR 005 – Session trên Redis, không dùng JWT** (mục 9.1).
- [x] **ADR 006 – Phạm vi Docker / Kubernetes / Kafka** (mục 3): Docker dùng thật; Kubernetes và Kafka chỉ để học ở giai đoạn C.
- [x] Hai lựa chọn ở mục 8.2: đăng ký trùng email trả `409 EMAIL_TAKEN`; không chặn đăng nhập khi email chưa xác thực.
- [x] Đăng nhập Google: không làm trong giai đoạn này; chỉ cân nhắc sau khi hoàn tất Must và Should, không cần tạo OAuth Client ID bây giờ.
- [x] BE1 (người làm chức năng admin) giữ quyền tạo tài khoản admin đầu tiên bằng script `make-admin`.
- [x] Cập nhật `docs/PLAN.md` mục 2 (phạm vi) và mục 7 (phân vai) theo quyết định trên.

Các quyết định ở mục này được chốt cho nhánh `dtm` ngày 18/11/2026. Người dùng đã xác nhận dùng Redis cho session.
