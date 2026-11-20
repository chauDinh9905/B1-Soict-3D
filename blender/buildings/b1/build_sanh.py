"""Dựng model Sảnh B1 vào file riêng blender/buildings/b1/B1_Sanh.blend.

Chạy từ thư mục gốc repo (Windows và Linux như nhau):
    blender -b -P blender/buildings/b1/build_sanh.py                              # tạo / dựng lại file
    blender -b blender/buildings/b1/B1_Sanh.blend -P blender/buildings/b1/build_sanh.py
    (tuỳ chọn: -- duong/dan/map.osm ; mặc định blender/data/map.osm)
Chạy nền (-b) thì lưu luôn vào B1_Sanh.blend. Chạy trong Blender có giao diện thì không tự lưu.
Dựng lại chỉ thay collection "B1_SanhRoot".
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(globals().get('__file__') or bpy.data.filepath))
OSM_PATH = globals().get('OSM_PATH') or os.path.join(HERE, '..', '..', 'data', 'map.osm')
if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 and sys.argv[sys.argv.index('--') + 1].endswith('.osm'):
    OSM_PATH = sys.argv[sys.argv.index('--') + 1]
OUT = os.path.join(HERE, 'B1_Sanh.blend')

if HERE not in sys.path:
    sys.path.insert(0, HERE)
for name in [m for m in sys.modules if m == 'b1' or m.startswith('b1.')]:
    del sys.modules[name]

from b1.main_sanh import run  # noqa: E402

run(OSM_PATH)
if bpy.app.background and not globals().get('NO_SAVE'):
    bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
    print('Đã lưu', OUT)
