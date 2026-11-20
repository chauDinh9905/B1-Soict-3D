"""Dựng lại rồi render các camera vào blender/renders/.

Chạy từ thư mục gốc repo (Windows và Linux như nhau):
    blender -b blender/buildings/b1/B1.blend -P blender/tools/render_views.py -- Cam_Ref Cam_Lobby Cam_Porch Cam_Aerial
    blender -b blender/buildings/b1/B1_Sanh.blend -P blender/tools/render_views.py -- Cam_SanhEntry Cam_SanhHust
File đang mở quyết định dựng gì: B1_Sanh.blend -> build_sanh.py, còn lại -> build_b1.py.
Có thể đặt một file .osm ngay sau "--" nếu không dùng blender/data/map.osm.
Script này không lưu .blend.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
SANH = os.path.basename(bpy.data.filepath).lower() == 'b1_sanh.blend'
SRC = os.path.join(BLENDER_DIR, 'buildings', 'b1', 'build_sanh.py' if SANH else 'build_b1.py')
exec(compile(open(SRC, encoding='utf-8').read(), SRC, 'exec'),
     {'__file__': SRC, '__name__': '__main__', 'NO_SAVE': True})

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
cams = [a for a in args if not a.endswith('.osm')] or (['Cam_SanhEntry'] if SANH else ['Cam_Ref'])
scene = bpy.context.scene
out_dir = os.path.join(BLENDER_DIR, 'renders')
os.makedirs(out_dir, exist_ok=True)
for name in cams:
    if SANH:
        plan = name == 'Cam_SanhPlan'
        bpy.data.collections['B1_Sanh_Ref'].hide_render = plan     # mặt tiền: hiện khi nhìn trong nhà
        for ob in bpy.data.collections['B1_Sanh'].objects:
            if 'Ceiling' in ob.name or ob.name in ('B1_SanhLights', 'B1_SanhReception'):
                ob.hide_render = plan and ob.name != 'B1_SanhReception'
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0 if plan else 0.35
    else:
        inside = name.startswith('Cam_Aud')   # interior shots: hide the exterior shell
        for ch in bpy.data.collections['B1_Building'].children:
            ch.hide_render = inside and ch.name != 'B1_Auditorium'
        bpy.data.collections['B1_Context'].hide_render = inside
        bpy.data.objects['B1_AudCeiling'].hide_render = name == 'Cam_AudPlan'
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.3 if inside else 1.0
    scene.camera = bpy.data.objects[name]
    scene.render.filepath = os.path.join(out_dir, name + '.png')
    bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects['Cam_SanhEntry' if SANH else 'Cam_Ref']
