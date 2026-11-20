"""Vẽ mặt bằng Sảnh B1 (tầng 1) thành SVG từ chính model sảnh: mặt cắt ngang ở cao 1 m trên sàn.
Không chép lại số đo nào: dựng sảnh bằng b1/sanh.py rồi cắt, nên sơ đồ luôn khớp model.

Chạy từ thư mục gốc repo:
    blender -b --factory-startup -P blender/tools/plan_lobby.py
Ra: docs/plans/b1_sanh_tang1.svg (cửa vào ở phía dưới, phía đông bên trái như sơ đồ cũ).
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
B1_DIR = os.path.join(os.path.dirname(HERE), 'buildings', 'b1')
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, 'docs', 'plans', 'b1_sanh_tang1.svg')
if B1_DIR not in sys.path:
    sys.path.insert(0, B1_DIR)
for name in [m for m in sys.modules if m == 'b1' or m.startswith('b1.')]:
    del sys.modules[name]

from b1 import layout, sanh  # noqa: E402
from b1.auditorium import fan_of  # noqa: E402
from b1.lobby import arc_frame, build_f1  # noqa: E402
from b1.main import reset_root  # noqa: E402
from b1.materials import make_materials  # noqa: E402
from b1.meshkit import collection  # noqa: E402

info = layout.build_parts()
arc = arc_frame()
root = reset_root('B1_PlanTmp')
make_materials()
coll = sanh.build_sanh(root, info, arc)
ref = collection(root, 'B1_PlanRef')
build_f1(arc, ref)
fr = sanh.Frame(fan_of(info))
ZCUT = sanh.Z0 + 1.0
SKIP = ('Joints', 'Lights', 'Ceiling', 'FloorPattern', 'Floor')
FLOORS = ('B1_SanhFloor', 'B1_SanhHallFloor', 'B1_SanhCorrFloor')
FILL = {'B1_SanhRed': '#c98f7f', 'B1_SanhGrey': '#b9bec4'}


def loc(p):
    x, y = fr.loc(p.to_2d())
    return x, y - fr.ya


def faces(ob):
    me = ob.data
    for poly in me.polygons:
        yield [ob.matrix_world @ me.vertices[i].co for i in poly.vertices], me.materials[poly.material_index].name


sections, floor_polys, pattern, steps = [], [], [], []
objs = [o for o in list(coll.objects) + list(ref.objects) if o.type == 'MESH']
for ob in objs:
    if ob.name in FLOORS:
        for vs, _ in faces(ob):
            if all(abs(v.z - sanh.Z0) < 1e-3 for v in vs):
                floor_polys.append([loc(v) for v in vs])
        continue
    if ob.name == 'B1_SanhFloorPattern':
        for vs, m in faces(ob):
            if all(v.z > sanh.Z0 + 0.001 for v in vs):
                pattern.append(([loc(v) for v in vs], FILL.get(m, '#ccc')))
        continue
    if any(k in ob.name for k in SKIP):
        continue
    for vs, _ in faces(ob):
        pts = []
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            if (a.z - ZCUT) * (b.z - ZCUT) < 0:
                t = (ZCUT - a.z) / (b.z - a.z)
                pts.append(loc(a.lerp(b, t)))
        if len(pts) >= 2:
            sections.append((pts[0], pts[1]))
        if ob.name == 'B1_SanhStair' and all(abs(v.z - vs[0].z) < 1e-4 for v in vs) and vs[0].z < ZCUT + 3.0 \
                and vs[0].z > sanh.Z0 + 0.01 and len(vs) == 4:
            steps.append([loc(v) for v in vs])

allp = [p for s in sections for p in s] + [p for poly in floor_polys for p in poly]
xmin, xmax = min(p[0] for p in allp), max(p[0] for p in allp)
dmin, dmax = min(p[1] for p in allp), max(p[1] for p in allp)
S = 30.0
PAD = 70
W = int((xmax - xmin) * S + 2 * PAD + 330)
H = int((dmax - dmin) * S + 2 * PAD + 90)


def X(x):          # xoay 180 độ: cửa vào ở dưới, đông bên trái
    return PAD + (xmax - x) * S


def Y(d):
    return PAD + 60 + (d - dmin) * S


def P(poly):
    return ' '.join(f'{X(x):.1f},{Y(d):.1f}' for x, d in poly)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="Segoe UI, Arial, sans-serif">',
       f'<rect width="{W}" height="{H}" fill="#fbfbfc"/>',
       f'<text x="{PAD}" y="40" font-size="24" font-weight="700" fill="#1f2d44">Mặt bằng Sảnh B1 – tầng 1</text>',
       f'<text x="{PAD}" y="64" font-size="14" fill="#5a6577">Cắt ngang ở cao 1 m trên sàn, sinh từ model '
       f'(blender/tools/plan_lobby.py)</text>']
for poly in floor_polys:
    svg.append(f'<polygon points="{P(poly)}" fill="#e4e6ea" stroke="none"/>')
for poly, col in pattern:
    svg.append(f'<polygon points="{P(poly)}" fill="{col}" stroke="none"/>')
for poly in steps:
    svg.append(f'<polygon points="{P(poly)}" fill="none" stroke="#8a93a3" stroke-width="0.8"/>')
for (x0, d0), (x1, d1) in sections:
    svg.append(f'<line x1="{X(x0):.1f}" y1="{Y(d0):.1f}" x2="{X(x1):.1f}" y2="{Y(d1):.1f}" '
               f'stroke="#1f2d44" stroke-width="1.6" stroke-linecap="round"/>')
for text, p in sanh.PLAN_LABELS:
    x, d = loc(p)
    svg.append(f'<text x="{X(x):.1f}" y="{Y(d):.1f}" font-size="14" font-weight="600" text-anchor="middle" '
               f'fill="#2a4e86" stroke="#fbfbfc" stroke-width="4" paint-order="stroke">{text}</text>')
# hướng bắc: trục y của model (bắc) -> toạ độ thiết kế
north = fr.loc(fr.fan.C + __import__('mathutils').Vector((0.0, 1.0)))
nx, nd = north[0], north[1] - fr.loc(fr.fan.C)[1]
cx, cy = W - 120, 130
svg.append(f'<circle cx="{cx}" cy="{cy}" r="34" fill="none" stroke="#1f2d44" stroke-width="1.5"/>')
svg.append(f'<line x1="{cx}" y1="{cy}" x2="{cx - nx * 30:.1f}" y2="{cy + nd * 30:.1f}" stroke="#b3141b" stroke-width="3"/>')
svg.append(f'<text x="{cx - nx * 48:.1f}" y="{cy + nd * 48 + 5:.1f}" font-size="16" font-weight="700" '
           f'text-anchor="middle" fill="#b3141b">N</text>')
sx, sy = W - 30 - 10 * S - 30, H - 40
for i in range(0, 11, 2):
    svg.append(f'<rect x="{sx + i * S:.1f}" y="{sy}" width="{S * 2:.1f}" height="6" '
               f'fill="{"#1f2d44" if i % 4 == 0 else "#fff"}" stroke="#1f2d44"/>' if i < 10 else '')
    svg.append(f'<text x="{sx + i * S:.1f}" y="{sy - 6}" font-size="12" text-anchor="middle">{i}</text>')
svg.append(f'<text x="{sx + 10 * S + 14:.1f}" y="{sy + 6}" font-size="12">m</text>')
notes = ['Đông = thang 3–4, tây = thang 1–2 (theo hướng chụp ảnh ref)',
         'Trần thấp 3.6 m: lễ tân, sảnh sau, hành lang; thông tầng ~6.9 m',
         f'Cốt sàn trong nhà +{sanh.Z0:.2f} m (bằng chiếu nghỉ ngoài cửa)']
for i, t in enumerate(notes):
    svg.append(f'<text x="{PAD}" y="{H - 52 + i * 18}" font-size="13" fill="#5a6577">{t}</text>')
svg.append('</svg>')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(svg))
print('Ghi', OUT, len(sections), 'đoạn cắt')
