"""Dựng file riêng của Sảnh B1 (B1_Sanh.blend).

Cùng footprint tham số (layout.py) với vỏ ngoài (main.py) nên toạ độ trùng khớp: glb sảnh đặt vào web là khớp ngay.
Collection:
  B1_Sanh      - model sảnh, được xuất ra web (tools/export_glb.py -- B1_Sanh ...)
  B1_Sanh_Ref  - mặt tiền tầng 1 (Lobby_F1) để nhìn tham chiếu khi dựng; không render, không xuất
  B1_Sanh_Rig  - nắng + bầu trời để render kiểm tra
"""
import bpy

from . import layout
from .lobby import arc_frame, build_f1, build_ring
from .main import reset_root
from .materials import make_materials
from .meshkit import collection
from .sanh import build_sanh
from .scene import setup_scene


def run(osm_path=None):
    # osm_path giữ cho tương thích lệnh cũ: footprint giờ là tham số (layout.py), OSM chỉ dùng để lên kế hoạch
    for name in ('Cube', 'Light', 'Camera'):          # đồ mặc định của file mới
        ob = bpy.data.objects.get(name)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)

    root = reset_root('B1_SanhRoot')
    make_materials()
    info = layout.build_parts()
    arc = arc_frame()
    coll = build_sanh(root, info, arc)
    ref = collection(root, 'B1_Sanh_Ref')
    build_f1(arc, ref)
    build_ring(arc, ref)
    ref.hide_render = True
    setup_scene(collection(root, 'B1_Sanh_Rig'), None, cameras=False)
    bpy.context.scene.camera = bpy.data.objects.get('Cam_SanhEntry')

    for c in (coll, ref):
        faces = sum(len(o.data.polygons) for o in c.objects if o.type == 'MESH')
        print(f'{c.name}: {len(c.objects)} objects, {faces} faces')
        for o in c.objects:
            print('  -', o.name)
