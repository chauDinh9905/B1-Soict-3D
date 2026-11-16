"""Xuất MỘT khối (một collection) ra .glb cho web.

Chạy từ thư mục gốc repo (Windows và Linux như nhau):
    blender -b blender/buildings/b1/B1.blend -P blender/tools/export_glb.py -- B1_F1 web/public/models/buildings/b1/floor1.glb

Chỉ xuất object nằm TRONG collection chỉ định (kể cả collection con):
- mesh hiển thị (bỏ object tắt render),
- các object đặc biệt Cam_*, POI_*, COL_*, ROOM_*, DOOR_* của RIÊNG khối đó, kể cả khi tắt render.
Bản cũ lấy Cam_/POI_/COL_ của cả file .blend nên xuất theo tầng bị trùng – đã sửa.

Script cũng cảnh báo DOOR_* có cha (tọa độ trong .glb sẽ là tọa độ cục bộ, script manifest đọc sai).
Mọi khối dùng chung một gốc tọa độ (tâm B1): KHÔNG di chuyển gốc từng collection trước khi xuất.

LƯU Ý: chưa chạy thử trên máy nhóm – mở kết quả bằng https://gltf-viewer.donmccurdy.com để kiểm tra,
rồi chạy `npm run manifest -- --check` (server/) để đối chiếu.
"""
import os
import sys

import bpy

SPECIAL = ('Cam_', 'POI_', 'COL_', 'ROOM_', 'DOOR_')

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(args) < 2:
    raise SystemExit('Cách dùng: ... -- <TenCollection> <duong/dan/ra.glb>')
COLL, OUT = args[0], os.path.abspath(args[1])

coll = bpy.data.collections.get(COLL)
if coll is None:
    raise SystemExit(f'Không thấy collection {COLL}')


def find_layer_collection(layer_coll, name):
    if layer_coll.collection.name == name:
        return layer_coll
    for child in layer_coll.children:
        found = find_layer_collection(child, name)
        if found:
            return found
    return None


# Collection bị loại khỏi view layer (ô tick bỏ trống) thì không chọn được object -> bật lại tạm thời.
view_layer = bpy.context.view_layer
lc = find_layer_collection(view_layer.layer_collection, COLL)
if lc is None:
    raise SystemExit(f'Collection {COLL} không nằm trong scene đang mở')
lc.exclude = False
lc.hide_viewport = False

for o in view_layer.objects:
    o.select_set(False)

picked = [o for o in coll.all_objects if o.name.startswith(SPECIAL) or not o.hide_render]
for o in picked:
    o.hide_set(False)
    o.hide_viewport = False
    o.select_set(True)

counts = {p: sum(o.name.startswith(p) for o in picked) for p in SPECIAL}
print(f'Xuất {len(picked)} object từ {COLL} -> {OUT}')
print('  ' + ', '.join(f'{p}*: {n}' for p, n in counts.items()))
for o in picked:
    if o.name.startswith('DOOR_') and o.parent is not None:
        print(f'  CẢNH BÁO: {o.name} có cha ({o.parent.name}) – hãy bỏ cha (Alt+P, Keep Transform)')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT,
    export_format='GLB',
    use_selection=True,
    export_yup=True,            # Blender Z-up -> glTF Y-up (x = đông, y = lên, z = nam)
    export_apply=True,          # áp dụng modifier
    export_cameras=True,
    export_lights=False,        # ánh sáng dựng lại trên web
    export_extras=True,         # custom property -> userData
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
)
print('Xong.')
