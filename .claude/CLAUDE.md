# B1Web – mô hình 3D nhà B1 (ĐH Bách khoa Hà Nội)

## Môi trường
- Nhóm 5 người, máy Windows và Linux. Blender 5.2 có trong PATH là `blender` trên mọi máy.
- Mọi lệnh chạy **từ thư mục gốc repo**, đường dẫn tương đối, dùng dấu `/` (chạy được cả PowerShell lẫn bash).
- Kế hoạch tổng của dự án: `docs/PLAN.md`; quy ước: `docs/CONVENTIONS.md`.

## Chạy dựng mô hình
```
blender -b blender/buildings/b1/B1.blend -P blender/buildings/b1/build_b1.py
```
- Script chỉ dựng lại collection `B1_OSM`; chạy lại nhiều lần không nhân đôi object (đã kiểm tra). Muốn lưu thì thêm `--python-expr "import bpy; bpy.ops.wm.save_mainfile()"`.
- Dựng + render: `blender -b blender/buildings/b1/B1.blend -P blender/tools/render_views.py -- Cam_Ref Cam_Lobby Cam_Porch Cam_Aerial` → ảnh vào `blender/renders/`. Script này không lưu .blend.
- Xuất cho web (3 glb, lệnh đầy đủ ở `README.md` gốc): `export_glb.py -- B1_Building .../b1.glb exclude=B1_Auditorium`, `export_glb.py -- B1_Auditorium .../b1_giangduong.glb noextra`, và sảnh `-- B1_Sanh .../b1_sanh.glb`.
- Camera: `Cam_Ref` (gần góc chụp ref.jpg), `Cam_Aerial`, `Cam_Lobby` (nhìn thẳng vành sảnh), `Cam_Porch` (dưới mái đón xe). Giảng đường: `Cam_AudStage`, `Cam_AudBalcony`, `Cam_AudRear`, `Cam_AudBoard`, `Cam_AudPlan`.
- Bản cũ trước khi tách module: `blender/buildings/b1/_backup/`.

## Nguồn gốc code (gộp 2026-11-20)
- Vỏ ngoài (`config`, `layout`, `wings`, `tower`, `rooftop`, `lobby`, `scene`) lấy từ nhánh thiết kế lượt 6–14 của user (repo cũ `B1Web`, khi đó chưa commit). Dựng từ code này ra **đúng** model user chốt (đã so từng object).
- Sảnh trong (`sanh.py`, `main_sanh.py`, `build_sanh.py`), giảng đường (`auditorium.py`), web viewer: từ bản của Kevin, đã chỉnh cho footprint tham số (xem mục Sảnh trong).

## Cấu trúc code
- `blender/buildings/b1/build_b1.py` – entry, nạp lại package `blender/buildings/b1/b1/` mỗi lần chạy.
- `blender/buildings/b1/b1/`: `config` (hằng số, cờ `BUILD_CONTEXT`), **`layout` (footprint tham số đối xứng, lượt 9)**, `osm`, `geom`, `meshkit` (MB + primitive), `materials`, `wings` (mỗi khối của layout = 1 object), `lobby` (sảnh chính, mặt ngoài), `tower` (tháp thang tròn), `rooftop`, `auditorium` (giảng đường tầng 3–4 trong vành), `sanh` (sảnh trong, file riêng), `context`, `scene`, `main`, `main_sanh`.
- Dữ liệu: `blender/data/map.osm` – B1 là way `184021007`, phần sảnh cong là building:part `1207082389`. **Từ lượt 9, OSM chỉ dùng để lên kế hoạch**: các kích thước gốc đã hardcode trong `layout.py` (góc V, trục, góc 90°, số tầng, độ võng cung). Chỉ `context` (đang tắt) còn đặt theo OSM nên không khớp footprint mới.
- `layout.build_parts()` trả dict cùng dạng dict building:part OSM cũ; phần sảnh (`ENTRANCE_PART`) có node tên `C` (góc V), `W_lobby`/`E_lobby` (2 đầu cung), `arc1..arc23`. `auditorium.fan_of(info)` dựng hình quạt theo **tên node**, không theo thứ tự điểm.

## Ảnh tham chiếu (`blender/buildings/b1/ref/`)
- `ref.jpg` – toàn cảnh mặt trước (vành tròn sảnh, tháp thang tròn, chữ B1).
- `116c18eb-…jpg` – vành tròn sảnh + mái đón xe cận cảnh.
- `047b7416-…jpg` – mái đón xe nhìn nghiêng, cột inox, tường kem tầng 1.
- `84666966-…jpg` – dưới mái đón xe: trần xám đậm, ô trần lõm, cửa kính khung đen, tường kem.
- `sanh.png` – sketch của user: TRÁI = mặt đứng mái đón xe (viền vát) + 2 cột tròn + thềm 2 bậc (+ bồn cây loe 2 bên – chưa làm); PHẢI = khung cửa kính sảnh chính, 5 ô × 3 hàng, hàng dưới có 2 bộ cửa đôi.

## Quyết định đã chốt với user
- Tòa nhà phải tách thành nhiều module con: cả file Python lẫn object/collection trong Blender ("nhiều mảnh ghép").
- (Lượt 7, user gọi là "lỗi chí mạng") Sảnh chính cao **4 tầng**: **tầng 1–2 vàng kem**, là khoảng lõm cao 2 tầng dưới vành (`BASE_LV = 2`, `BASE_H` trong `b1/lobby.py`; mái đón xe nằm sát dưới vành). **Tầng 3–4 là vành tròn trắng.** Các cánh nhà khác trắng.
- Cao độ cửa sổ sảnh phải **khớp với cánh nhà bên cạnh**: dùng cùng bậu/đầu cửa (`fb + 0.95`, `ft - 0.35`) và cùng băng sàn. Đường chia hàng trong vành nằm đúng chiều cao thanh ngang của cụm cửa sổ cánh (`RING_TRANSOM = 0.26`). Kính tầng 1/2 của phần kem (`BANK_Z`) cũng theo tầng của cánh.
- Mái đón xe: tấm thẳng xám đậm, viền vát, 2 cột inox tròn, thềm đá.
- (Lượt 12) Phần giữa sảnh đang được user chỉnh **từng bước**: `ENTRY_SCALE` trong `b1/lobby.py` (hiện 1.25) giãn tường kem 2 bên khung cửa, mái đón xe, khoảng cách cột và đèn. Khung kính cửa chính tách riêng: `DOOR_BAY_W = 2.6` (khung 13 m), để nhìn từ trước vẫn rộng hơn 2 cột. Bậc thềm tự rộng theo khung cửa. Cung sảnh giữ nguyên nên kính 2 bên tự ngắn lại. Tường kem 2 bên khung cửa có mặt trước bám theo cung (lùi 0.45 m), không được nhô ra khỏi vòng tròn vành (lượt 14).
- Hướng: trục y của model = hướng bắc. Ảnh ref chụp từ bãi xe phía bắc/tây bắc nên **bên trái ảnh = phía đông**. Vành sảnh: P[0] ở đầu tây, P[NS] ở đầu đông.
- (Lượt 9, user: "lỗi nghiêm trọng") Tòa nhà phải **đối xứng gương trái/phải** và **mỗi cụm cửa sổ bằng nhau, không méo**. Code tự dựng viền tòa nhà trong `b1/layout.py`, cả 2 cánh sinh từ cùng một hàm `arm_pt(side, s, t)`.
  - Mỗi cánh, từ góc V ra ngoài: đoạn tường trơn 6 m sau tháp thang (`TOWER_ZONE`, `PLAIN_EDGES`, không lan can), rồi khối **10T có 3 ô, 8T có 1 ô, 5T có 1 ô** mặt trước (`BLOCKS`). (Lượt 10: thử 3/4/5 ô thì cánh quá dài, user bỏ "khối thừa", chốt 3/1/1.)
  - (Lượt 11) **Mỗi ô cửa trong cụm phải vuông**: `BAY_W = 3 × 2.3 + 2 × 0.5 + 0.5 = 8.4 m` (`config.py`). Cửa tầng điển hình cao 2.3 m nên rộng 2.3 m. Cánh dài 48 m, gần đúng OSM.
  - Bề dày cánh `ARM_W` = 12.44 m (OSM). Mặt sau: 10T có `BACK_BAYS` = 5 ô chạy tới góc ngoài, phần dư ~1.64 m là trụ góc đặc (lượt 14, user thay tường lõi có cửa nhỏ bằng cụm cửa), 8T 1 ô, 5T 1 ô.
  - Ảnh 7 (user): 3 cụm của khối 10T đều lộ cạnh tháp. Sảnh che vùng tháp + 2 ô (`LOBBY_BAYS`).
- Cung sảnh: đi qua 2 điểm cuối sảnh trên mặt trước 2 cánh, đỉnh cung nằm trên trục, `LOBBY_BULGE = 0.30` (theo OSM). R ≈ 29.3 m, dài cung ≈ 34.1 m (user cho phép sảnh to hơn). Hàm `layout.lobby_arc`.
- Mái: 2 hộp kỹ thuật cùng cỡ, đối xứng (`layout.PENTHOUSE_EDGES`). Cột ăng-ten, bồn nước và chữ B1 vẫn ở phía tây như ảnh thật.
- Camera `Cam_Ref`/`Cam_Aerial` đặt tương đối theo `layout.CORNER`, khoảng cách nhân `ARM_LEN / 49.3` (hệ số so với footprint OSM).
- (Lượt 6, thay quyết định cũ "lệch đông") Mặt trước sảnh **ĐỐI XỨNG**: cửa chính + mái đón xe nằm giữa cung (`ENTRY_F = 0.5`).
- (Lượt 13) Kính tháp thang tròn: 1 màu tối đồng nhất (`B1_GlassCluster`, hằng `GLASS` trong `b1/tower.py`), không random. Cột cửa sổ nhỏ trên mặt hồi nằm **sát mép phía mặt trước** (`layout.GABLE_WIN_T = 0.22`, `gable_win_t`), giống cửa tầng 9–10 dưới chữ B1. `build_wings(info, coll, layout)` nhận cả module layout.
- (Lượt 6, lượt 13 tăng số cột) Cửa sổ vành = tường trơn + 3 cụm lưới đối xứng (`RING_WINDOWS` trong `b1/lobby.py`): trái 5 cột, giữa 9 cột, phải 5 cột. Đố cửa chia đều theo cung (không bám điểm mẫu). Mỗi cụm có 5 hàng (`ring_rows`): 2 hàng kính tầng 3, **hàng 3 (từ trên xuống) nằm ở sàn giữa tầng 3 và 4 nên dùng material tường `B1_Wall`**, 2 hàng kính tầng 4. (Lượt 8) Đỉnh vành **không được nhô lên che cửa sổ tầng 5 của cánh**: cornice đặt ngay trên cửa sổ tầng 4 (`HE - 0.3`), đỉnh lan can là `HE + 0.9` = 16.2 m, thấp hơn bậu cửa sổ tầng 5 (16.25 m). Không còn gờ lõm.
- (Lượt 8) Kính tầng 1–2 mỗi bên cửa chính được **gộp thành 1 cụm**, 5 ô × số unit (hiện 10 ô/dải), tường kem ngoài/trong đối xứng gương (`f1_layout` → `units` = `(f0, f1, walls, panes)`, `shop_unit`, `unit_split`). Mái tháp thang nâng 3 cm trên mái cánh để không lộ viền chữ L. Khung lưới chạy xuyên qua cả hàng tường.
- (Lượt 6) Mái 10 tầng: không có lan can ở 2 cạnh trong chữ V giáp sảnh (tham số `parapet` của `facade_bays`). User coi đó là "khối tường thừa trên sân thượng".
- `CLUSTER_ALL = True` trong `b1/wings.py`: mọi mặt đứng nhịp (cả mặt sau) dùng cụm cửa sổ. Mặt hồi vẫn dùng `strip_window`.
- Trước mắt chỉ làm tòa nhà: không vẽ cây/bồn cây; context (đường, xe, nhà xung quanh) tắt mặc định (`BUILD_CONTEXT=False`).

## Cập nhật (lượt 2)
- Bậc thềm sảnh: 5 bậc (`N_STEPS` trong `b1/lobby.py`).
- Cụm cửa sổ (sketch user, `sanh.png`-style "mỗi cụm cửa sổ"): mỗi nhịp = 3 cửa sổ giống hệt nhau (dải trên + 2 ô dưới) ngăn bởi 2 panel đứng hẹp viền dày; tất cả dùng 1 material `B1_GlassCluster` (không random). Hàm `cluster_window` trong `b1/wings.py`.
- Kính tầng 1 hai bên cửa chính (sketch lượt 3): mỗi "unit" = tường kem | dải kính trên (5 ô) | dải tường kem ngang | dải kính dưới (5 ô) | tường kem; hàm `shop_unit` trong `b1/lobby.py` (`UNIT_W`, `BANK_Z`).
- Cụm cửa sổ (chốt lượt 5): 3 ô cửa (mỗi ô có nẹp giữa), giữa 2 ô liền kề là 1 panel chữ nhật hẹp (`CLUSTER_PANEL_W = 0.5`) cao suốt chiều cao cửa, **viền panel mỏng bằng viền cửa sổ** (không dày hơn), đường ngang (transom) chạy xuyên qua cả panel. User muốn làm đúng sát hình họ gửi, đừng tự thêm chi tiết.

## Mặt ngoài tầng 1–2 nối với sảnh trong (gộp 2026-11-20)
- Kính sảnh nhìn xuyên được: `B1_GlassLobby` alpha 0.3, **không còn tấm nền đen sau kính**.
- Cánh cửa đôi là object riêng `Lobby_F1_Doors` có custom property `noCollide` → web (`WalkMode`) cho đi xuyên. Dải sọc xanh–đỏ–xanh ngang tầm mắt trên khung cửa.
- `Lobby_F1_Soffit` chỉ phủ **dải ngoài trời** giữa mép vành và mặt kính lõm (kể cả hốc cửa chính), ở `BASE_H`. Phía sau kính là trần của sảnh trong; phía trên là giảng đường.

## Sảnh trong (`B1_Sanh.blend`, code `b1/sanh.py`)
- Dựng: `blender -b blender/buildings/b1/B1_Sanh.blend -P blender/buildings/b1/build_sanh.py` (tự lưu .blend). Render: `render_views.py -- Cam_SanhPlan Cam_SanhEntry Cam_SanhHust Cam_SanhHall Cam_SanhLifts34 Cam_SanhLifts12 Cam_SanhBack Cam_SanhPortal`. Mặt bằng SVG: `blender -b --factory-startup -P blender/tools/plan_lobby.py`. Xuất web: `export_glb.py -- B1_Sanh web/public/models/buildings/b1/b1_sanh.glb`.
- Dùng cùng `layout.build_parts()` + `lobby.arc_frame()` với vỏ ngoài nên glb sảnh gắn thẳng vào tòa nhà, không cần dịch.
- Sảnh thông tầng cao tới `ZA` (dưới sàn giảng đường), đúng bằng khối kem 2 tầng bên ngoài: lớp ốp mặt tiền nhìn từ trong (mép tường kem, dải xám giữa 2 băng kính, tường 2 bên cửa) chạy thẳng `Z0 → ZA`. Vành trắng nằm trên trần sảnh nên **không có lớp ốp tường vành** trong sảnh. Trần sảnh dừng ngay sau mặt kính (cùng đường biên với sàn).
- Ảnh ref nội thất nằm ngoài repo (thư mục `ref` của user, 23 ảnh). Mỗi camera ghi tên ảnh nó bám theo ở comment trong `add_lights_and_cameras`.
- Bố cục (chốt theo sketch user 2026-11-18): sau 2 cột trắng ở lỗ mở là **sảnh sau hình chữ nhật, tường song song trục quạt** (class `Hall`, toạ độ Frame x đông / d bắc). Tường đông: thang 3 rồi 4 (bắc→nam), cầu thang chữ U góc đông nam. Tường tây: thang 2 rồi 1 + cửa đơn. Giữa: quầy lễ tân chữ L (móc ở đầu đông) + tường logo HUST, phòng 104 sau quầy (cửa sổ + cửa nhìn ra lối đi cửa sau). Tường sau: cửa sau ở cuối lối đi giữa cầu thang và phòng 104, 2 cửa đôi ở phần tây.
- Hai dải chéo dọc cạnh quạt giờ là **hành lang cánh nhà, không có thang máy**, mở vào sảnh sau ở miệng (vuông góc cạnh quạt). Miệng đông có vách kính cửa đôi, miệng tây để trống.
- Ảnh 910316906 là **phía đông** (thang 3–4), c763a1a8 là phía tây (user xác nhận). Không có hành lang riêng chạy thẳng về tây. Vách kính phía đông đã đúng, không sửa.
- **Phần tây sảnh sau theo lưới 45° của cánh tây** (toạ độ `side(1, s, q)`, ảnh a6f71652 + c763a1a8): tường thang 1–2 nằm trên đường miệng hành lang chéo tây kéo dài (s = s0), vuông góc tường ngoài hành lang → **góc lồi 90°** ở đầu thang 2. Cạnh có 2 cửa đôi chạy song song hành lang (q = `Hall.Q4`, dài ~8 m) từ P4 (cuối tường thang) về P3; cạnh P3 → P2 (`P23`) song song tường thang, tới mặt tây phòng 104 (`P2_D`). Nét cong góc trên phải sketch chính là đoạn này. Camera kiểm tra: `Cam_SanhLifts12` (a6f71652), `Cam_SanhCorrW` (c763a1a8).
- Vị trí chỉnh nhanh ở đầu `sanh.py`: `HALL_S`, `LIFTS_E/LIFTS_W`, `MARBLE_D`, `R104_X`, `LOGO_D`, `COUNTER_D`, `WEST_DOORS`, `BACK_DOOR_A`. Các số này đo từ đỉnh quạt A / cạnh quạt, chỉnh trên quạt OSM cũ (nhỏ hơn); quạt tham số to hơn nên sảnh thông tầng rộng hơn, sảnh sau giữ nguyên kích thước. Bản trước khi đổi: `_backup/sanh_v1.py`, `_backup/B1_Sanh_v1.blend`, `_backup/b1_sanh_v1.glb`.

## Giảng đường (`b1/auditorium.py`, trong `B1.blend`)
- Xuất thành model riêng `b1_giangduong.glb` (collection `B1_Auditorium`, khai báo trong `interiors` của `b1.json`, vào bằng `Cam_AudRear`); `b1.glb` loại nó bằng `exclude=`.
- Tầng 3–4 trong vành (sàn `level_top(2)` = 8.1 m). Tường cong phía sau đứng ngay sau mặt trong tường vành (`RING_T`), không che cửa sổ vành.
- Mọi bán kính tính tương đối theo quạt: hàng ghế đầu cách tường sân khấu `ROW0_GAP`; số hàng tầng dưới tự tính, giới hạn để dưới sàn ban công còn `HEADROOM` = 2.2 m; phần còn lại tới tường sau là lối đi ngang ở cao độ hàng cuối. Ban công 5 hàng sát tường sau. Đèn/camera đặt theo tỉ lệ sâu hội trường (`rr(f)`).
