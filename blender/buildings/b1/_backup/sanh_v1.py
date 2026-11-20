"""Sảnh B1 (tầng 1): model riêng, dựng vào B1_Sanh.blend, xuất ra web/public/models/buildings/b1/b1_sanh.glb.

Bố cục theo ảnh ref (C:/.../ref, 15 ảnh) và sơ đồ đã chốt với user:
  - Sảnh thông tầng: phần hình quạt từ lỗ mở (d = D_OPEN) tới mặt kính cong. Tường ốp tấm trắng ngà,
    ron đen: ron đứng không đều, ron ngang so le theo từng mảng. Mảng tường trên lỗ mở có khe dọc lõm.
    Hai cổng má sâu trên hai tường bên. Sàn granite xám đậm + hoa văn ô bậc thang đỏ/xám.
  - Khu lễ tân trần thấp (ZC): phần quạt sát đỉnh, trần xám đậm, LED vạch toả tia. Quầy thẳng + tường logo.
  - Hai sảnh thang (dải hành lang dọc hai cạnh quạt): đông = thang 3–4, tây = thang 1–2 (theo hướng chụp ảnh).
    Tường thang ốp đá trắng vân vàng, cửa inox; trần LED vạch chéo + đèn tròn.
  - Sảnh cầu thang sau đỉnh quạt: cầu thang chữ U, tấm chắn hoa văn dưới vế 2, cửa sau, cửa sổ chiếu nghỉ.
Bỏ đồ rời (ghế, chậu cây, vách bình phong, TV) theo yêu cầu user.

Ba hệ toạ độ 2D (đều ra toạ độ thế giới của tòa nhà, nên glb sảnh khớp glb vỏ ngoài):
  Frame (x, d) : x hướng đông, d dọc trục quạt tính từ đỉnh A (xem class Frame).
  side(k, s, q): dải dọc cạnh quạt k (0 = đông, 1 = tây); s dọc cạnh tính từ A, q ra ngoài tính từ mặt
                 ngoài tường quạt (đường OSM). Tường quạt nằm ở q ∈ [-T, 0].
  rear(a, b)   : ô phía sau đỉnh; a dọc pháp tuyến ngoài cạnh đông, b dọc pháp tuyến ngoài cạnh tây.
"""
import bisect
import math
import os
import random

import bpy
from mathutils import Vector

from .auditorium import Fan
from .config import ENTRANCE_PART, GROUND_H, level_top
from .lobby import (BANK_Z, LANDING_Z, NS, REC, RING_WINDOWS, SHOP_WALL_D, f1_layout, lerp_arc, unit_split)
from .materials import image_material, principled
from .meshkit import MB, box_uv, collection, curved_solid, cylinder, prism

HERE = os.path.dirname(os.path.abspath(__file__))
MARBLE_PATH = os.path.join(os.path.dirname(HERE), 'textures', 'marble.jpg')

# ---------------------------------------------------------------- kích thước (m)
T = 0.35                    # dày tường quạt
Z0 = LANDING_Z              # cốt sàn trong nhà = chiếu nghỉ ngoài cửa (5 bậc)
ZC = Z0 + 3.6               # trần thấp: lễ tân, sảnh thang
ZA = level_top(2) - 0.46    # trần thông tầng, dưới đáy sàn giảng đường (7.70) để không trùng mặt
ZS = Z0 + 6.6               # trần giếng cầu thang
D_OPEN = 4.3                # mặt lỗ mở từ sảnh thông tầng vào khu lễ tân
UPPER_T = 0.6               # dày mảng tường trên lỗ mở
WALL = 0.25                 # tường trong
CORR = 3.6                  # rộng sảnh thang
S_END = 15.7                # sảnh thang cắt ở đây (sau cổng má sâu), tường + cửa
OPEN_S = (11.6, 14.1)       # cổng má sâu trên tường bên sảnh thông tầng (s)
PORTAL_H = 3.2
LIFT_W, LIFT_H = 1.1, 2.2
LIFTS = {0: [('4', 2.6), ('3', 4.9)], 1: [('1', 2.6), ('2', 4.9)]}
MARBLE_S = {0: (1.5, 6.1), 1: (1.6, 6.0)}
X_C = -0.6                  # đường giữa khu lễ tân (đỉnh quạt lệch tây so với trục)
LOGO_D, COUNTER_D = 1.0, 2.6
# sảnh cầu thang (a, b)
REAR_A, REAR_B = 6.2, 6.2
STAIR_A1, STAIR_A2 = (1.9, 3.7), (3.9, 5.7)
STAIR_B0 = 0.8
N_RISE, TREAD = 12, 0.28
STORY = level_top(1) - Z0   # sàn tầng 2 = 4.5
PASS_A = 1.7                # lối đi tới cửa sau, giữa tường tây và cầu thang

PLAN_LABELS = []            # (chữ, điểm 2D) cho tools/plan_lobby.py


def make_sanh_materials():
    principled('B1_SanhPanel', (0.86, 0.85, 0.81), 0.55)            # tấm ốp trắng ngà
    principled('B1_SanhPaint', (0.90, 0.90, 0.88), 0.8)             # tường sơn trắng
    principled('B1_SanhJoint', (0.03, 0.03, 0.035), 0.6)
    principled('B1_SanhSlot', (0.50, 0.50, 0.50), 0.8)              # khe dọc lõm
    principled('B1_SanhGranite', (0.085, 0.09, 0.095), 0.15, coat=0.6)
    principled('B1_SanhRed', (0.30, 0.10, 0.07), 0.15, coat=0.6)
    principled('B1_SanhGrey', (0.24, 0.25, 0.26), 0.15, coat=0.6)
    principled('B1_SanhCeiling', (0.86, 0.86, 0.85), 0.9)
    principled('B1_SanhSoffit', (0.20, 0.21, 0.23), 0.6)
    principled('B1_SanhBand', (0.33, 0.34, 0.36), 0.5)              # dải xám giữa hai băng kính
    principled('B1_SanhLed', (1.0, 1.0, 1.0), 0.3, emission=((0.95, 0.97, 1.0), 12.0))
    principled('B1_SanhLogo', (0.93, 0.93, 0.94), 0.08, coat=0.6)
    principled('B1_SanhBronze', (0.50, 0.36, 0.22), 0.35, 0.8)
    principled('B1_SanhCounter', (0.92, 0.92, 0.91), 0.4)
    principled('B1_SanhDeskTop', (0.03, 0.03, 0.035), 0.25)
    principled('B1_SanhStairStone', (0.30, 0.30, 0.31), 0.3)
    principled('B1_SanhWood', (0.13, 0.055, 0.03), 0.4)
    principled('B1_SanhAlu', (0.86, 0.87, 0.87), 0.4, 0.3)
    principled('B1_SanhAluGrey', (0.30, 0.31, 0.32), 0.4, 0.5)
    principled('B1_SanhSteelDark', (0.07, 0.07, 0.08), 0.4, 0.6)
    principled('B1_SanhFrosted', (0.72, 0.76, 0.77), 0.3)
    principled('B1_SanhGlass', (0.55, 0.65, 0.66), 0.05, alpha=0.25)
    principled('B1_SanhDaylight', (0.85, 0.92, 0.85), 0.5, emission=((0.85, 0.93, 0.85), 2.5))
    principled('B1_SanhScreen', (0.02, 0.02, 0.025), 0.3)
    if not os.path.exists(MARBLE_PATH):
        make_marble(MARBLE_PATH)
    image_material('B1_SanhMarble', MARBLE_PATH, rough=0.12, coat=0.5)


def make_marble(path, size=1024, seed=5):
    """Ảnh đá trắng vân vàng, lặp liền mép (tileable), sinh bằng numpy để không cần bake."""
    import numpy as np
    rng = np.random.default_rng(seed)

    def vnoise(res):
        g = rng.random((res, res))
        t = np.arange(size) * res / size
        i0 = t.astype(int) % res
        i1 = (i0 + 1) % res
        f = t - np.floor(t)
        f = f * f * (3 - 2 * f)
        a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
        b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
        return a * (1 - f)[:, None] + b * f[:, None]

    turb = sum(vnoise(r) * a for r, a in ((3, 0.5), (6, 0.25), (12, 0.13), (24, 0.07), (48, 0.03)))
    y, x = np.mgrid[0:size, 0:size] / size
    v1 = np.sin(2 * np.pi * (x + 2 * y) + turb * 9.0)
    v2 = np.sin(2 * np.pi * (3 * x - y) + turb * 13.0 + 1.3)
    gold = np.exp(-(np.abs(v1) / 0.035) ** 2)
    grey = np.exp(-(np.abs(v2) / 0.02) ** 2) * 0.6
    base = 0.93 + (vnoise(32) - 0.5) * 0.03
    r = base - gold * 0.30 - grey * 0.25
    g = base - gold * 0.42 - grey * 0.25
    b = base - gold * 0.60 - grey * 0.22
    rgba = np.stack([r, g, b, np.ones_like(r)], axis=-1).clip(0, 1).astype(np.float32)
    img = bpy.data.images.new('B1_Marble', size, size)
    img.pixels.foreach_set(rgba.ravel())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.filepath_raw = path
    img.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = 88
    img.save()
    bpy.data.images.remove(img)


# ---------------------------------------------------------------- hình học
class Frame:
    """Toa do thiet ke (X, d) <-> toa do the gioi."""

    def __init__(self, fan):
        self.fan = fan
        self.ax = Vector((math.cos(fan.th0), math.sin(fan.th0)))
        self.rt = Vector((math.sin(fan.th0), -math.cos(fan.th0)))
        self.ya = self.loc(fan.A)[1]
        self.lines = []
        for p0, d in fan.lines:
            x, y = self.loc(p0)
            self.lines.append(((x, y - self.ya), (d.dot(self.rt), d.dot(self.ax))))

    def loc(self, p):
        v = p - self.fan.C
        return v.dot(self.rt), v.dot(self.ax)

    def w(self, x, d):
        return self.fan.C + self.rt * x + self.ax * (self.ya + d)

    def xl(self, k, d):
        (px, pd), (dx, dd) = self.lines[k]
        return px + dx * (d - pd) / dd

    def dd(self, p):
        return self.loc(p)[1] - self.ya


class Geo:
    def __init__(self, fan, arc):
        self.fan, self.arc, self.fr = fan, arc, Frame(fan)
        self.A = fan.A.copy()
        self.dir = [fan.lines[k][1].copy() for k in (0, 1)]
        self.n_in = [(fan.lines[k][0] - fan.A).normalized() for k in (0, 1)]
        self.O = [-n for n in self.n_in]
        self.lay = f1_layout(arc['P'], arc['N'])

    def side(self, k, s, q):
        return self.A + self.dir[k] * s + self.O[k] * q

    def rear(self, a, b):
        return self.A + self.O[0] * a + self.O[1] * b

    def s_at_d(self, k, d, q=0.0):
        base = self.fr.dd(self.A + self.O[k] * q)
        return (d - base) / self.dir[k].dot(self.fr.ax)

    def osm(self, k, d):
        return self.side(k, self.s_at_d(k, d), 0.0)


def quad(f, s0, s1, q0, q1):
    return [f(s0, q0), f(s1, q0), f(s1, q1), f(s0, q1)]


def clip(poly, p0, nrm):
    """Giữ phần đa giác có (p - p0)·nrm >= 0."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = (a - p0).dot(nrm), (b - p0).dot(nrm)
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            out.append(a.lerp(b, da / (da - db)))
    return out


def inside(poly, p):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a.y > p.y) != (b.y > p.y) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x:
            c = not c
    return c


def cut(intervals, a, b):
    out = []
    for x0, x1 in intervals:
        if b <= x0 or a >= x1:
            out.append((x0, x1))
            continue
        if a > x0:
            out.append((x0, a))
        if b < x1:
            out.append((b, x1))
    return out


def wall_run(mb, f, s0, s1, q0, q1, z0, z1, mat, holes=()):
    """Tường dọc s (f(s, q) -> điểm 2D), chừa lỗ (sa, sb, za, zb)."""
    cur = s0
    for sa, sb, za, zb in sorted(h for h in holes if h[1] > s0 and h[0] < s1):
        if sa > cur:
            prism(mb, quad(f, cur, sa, q0, q1), z0, z1, mat)
        if za > z0:
            prism(mb, quad(f, sa, sb, q0, q1), z0, za, mat)
        if zb < z1:
            prism(mb, quad(f, sa, sb, q0, q1), zb, z1, mat)
        cur = max(cur, sb)
    if cur < s1:
        prism(mb, quad(f, cur, s1, q0, q1), z0, z1, mat)


def panel_joints(mb, f, s0, s1, qf, sgn, z0, z1, rnd, holes=(), zh=(Z0 + 3.5, Z0 + 3.9), slots=None):
    """Ron tấm ốp trên mặt tường q = qf (phòng ở phía sgn): ron đứng khoảng cách ngẫu nhiên,
    ron ngang chia vài đoạn, mỗi đoạn một cao độ (gãy bậc như ảnh). slots=(sa, sb): bỏ ron, để khe."""
    JW, JD = 0.009, 0.006

    def bar(sa, sb, za, zb, mat='B1_SanhJoint', depth=JD):
        prism(mb, [f(sa, qf), f(sb, qf), f(sb, qf + sgn * depth), f(sa, qf + sgn * depth)], za, zb, mat, bottom=False)

    def free(s, za, zb):
        segs = [(za, zb)]
        for ha, hb, hz0, hz1 in holes:
            if ha - 0.05 <= s <= hb + 0.05:
                segs = cut(segs, hz0, hz1)
        return segs

    def skip(s):
        return slots is not None and slots[0] - 0.1 <= s <= slots[1] + 0.1

    xs, s = [], s0 + rnd.uniform(0.3, 1.0)
    while s < s1 - 0.3:
        if not skip(s):
            xs.append(s)
        s += rnd.uniform(0.45, 1.45)
    n_cut = min(len(xs), rnd.randint(1, 3))
    cuts = sorted(rnd.sample(xs, n_cut)) if n_cut else []
    edges = [s0] + cuts + [s1]
    base = rnd.uniform(*zh)
    hs = [base + rnd.uniform(-0.2, 0.2) for _ in range(len(edges) - 1)]

    def h_at(s):
        return hs[max(0, min(len(hs) - 1, bisect.bisect_right(edges, s) - 1))]

    for i in range(len(edges) - 1):
        pieces = [(edges[i], edges[i + 1])]
        if slots:
            pieces = cut(pieces, slots[0], slots[1])
        for ha, hb, hz0, hz1 in holes:
            if hz0 - 0.05 <= hs[i] <= hz1 + 0.05:
                pieces = cut(pieces, ha - 0.02, hb + 0.02)
        for pa, pb in pieces:
            bar(pa, pb, hs[i] - JW, hs[i] + JW)
    upper = []
    for s in xs:
        h = h_at(s)
        for za, zb in free(s, z0, h):
            bar(s - JW, s + JW, za, zb)
        if s in cuts or rnd.random() < 0.7:
            upper.append(s)
    extra = [(a + b) / 2 + rnd.uniform(-0.2, 0.2) for a, b in zip([s0] + upper, upper + [s1]) if b - a > 1.7]
    for s in upper + extra:
        if not skip(s):
            for za, zb in free(s, h_at(s), z1):
                bar(s - JW, s + JW, za, zb)
    if slots:                                   # khe dọc treo từ trần, dài ngắn khác nhau
        s = slots[0] + rnd.uniform(0.1, 0.3)
        while s < slots[1] - 0.1:
            bar(s - 0.018, s + 0.018, z1 - rnd.uniform(1.2, 3.1), z1, 'B1_SanhSlot', 0.004)
            s += rnd.uniform(0.22, 0.55)


def seg_rect(mb, p, q, w, z0, z1, mat):
    d = (q - p).normalized()
    n = Vector((-d.y, d.x)) * (w / 2)
    prism(mb, [p - n, q - n, q + n, p + n], z0, z1, mat)


def text_mesh(mb, body, size, base, right, out, z, mat, align='LEFT', extrude=0.006):
    """Chữ nổi dựng từ font mặc định, dán vào mặt tường (right: chiều đọc, out: pháp tuyến ra phòng)."""
    cu = bpy.data.curves.new('B1_tmp_text', 'FONT')
    cu.body, cu.size, cu.extrude, cu.align_x = body, size, extrude, align
    ob = bpy.data.objects.new('B1_tmp_text', cu)
    bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    for poly in me.polygons:
        pts = []
        for vi in poly.vertices:
            v = me.vertices[vi].co
            p2 = base + right * v.x + out * (v.z + extrude)
            pts.append((p2.x, p2.y, z + v.y))
        nr = right * poly.normal.x + out * poly.normal.z
        mb.face(pts, mat, (nr.x, nr.y, poly.normal.y))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)


# ---------------------------------------------------------------- mặt tiền cong nhìn từ trong
def arc_at_s(arc, s_of, s):
    P, N = arc['P'], arc['N']
    i = max(0, min(NS - 1, bisect.bisect_right(s_of, s) - 1))
    t = (s - s_of[i]) / (s_of[i + 1] - s_of[i])
    return P[i].lerp(P[i + 1], t), N[i].lerp(N[i + 1], t).normalized()


def facade_line(g, d_arc, d_flank=None, d_door=None):
    """Đường phía trong mặt tiền, từ đầu đông sang đầu tây. Trong khối cửa vào dùng mặt phẳng tiếp tuyến."""
    lay, arc = g.lay, g.arc
    c0, u, n = lay['c0'], lay['u'], lay['n']
    s_of = [(p - c0).dot(u) for p in arc['P']]
    half, zb = lay['half'], lay['zone'] + 0.15
    eps = 1e-4
    ss = set(s_of)
    if d_flank is not None:
        ss |= {sg * v + e for sg in (-1, 1) for v in (half, zb) for e in (-eps, eps)}

    def pt(s):
        if d_flank is not None and abs(s) < half:
            return c0 + u * s + n * d_door
        if d_flank is not None and abs(s) < zb:
            return c0 + u * s + n * d_flank
        p, nn = arc_at_s(arc, s_of, s)
        return p + nn * d_arc
    return [pt(s) for s in sorted(ss, reverse=True) if s_of[0] <= s <= s_of[-1]]


def fan_region(g, d_from, boundary):
    """Phần quạt từ d_from tới đường biên mặt tiền, cắt theo hai đường OSM."""
    poly = [g.osm(0, d_from)] + boundary + [g.osm(1, d_from)]
    for k in (0, 1):
        poly = clip(poly, g.A, g.n_in[k])
    return poly


# ---------------------------------------------------------------- các phần
def build_atrium(g, coll, rnd):
    fr = g.fr
    floor, pat = MB('B1_SanhFloor'), MB('B1_SanhFloorPattern')
    walls, joints, ceil = MB('B1_SanhWalls'), MB('B1_SanhJoints'), MB('B1_SanhCeiling')

    # sàn: cắt sát mặt kính (-0.82), trong khối cửa vào tới mặt khung cửa (REC) và mặt tường hai bên cửa
    region = fan_region(g, D_OPEN, facade_line(g, SHOP_WALL_D[0] + 0.48, REC - 1.0, REC))
    prism(floor, region, 0.0, Z0, 'B1_SanhGranite', bottom=False)
    # hoa văn: ô 1.2 m thẳng theo lưới sàn, chuỗi ô đỏ bậc thang chéo + ô xám cạnh chuỗi
    cell = 1.2
    for i in range(-12, 13):
        for j in range(0, 14):
            x0, d0 = X_C + 0.3 + i * cell, D_OPEN + 0.9 + j * cell
            corners = [fr.w(x0, d0), fr.w(x0 + cell, d0), fr.w(x0 + cell, d0 + cell), fr.w(x0, d0 + cell)]
            if not all(inside(region, c) for c in corners) or not all(
                    (c - g.A).dot(g.n_in[k]) > 0.9 for c in corners for k in (0, 1)):
                continue
            m4 = (i + j) % 4          # dải chéo bậc thang: đỏ, xám, nền, nền
            if m4 == 0:
                mat = 'B1_SanhRed'
            elif m4 == 1:
                mat = 'B1_SanhGrey'
            else:
                continue
            prism(pat, corners, Z0, Z0 + 0.004, mat, bottom=False)

    # tường hai bên (thông tầng), cổng má sâu, cột ở đầu tường cạnh lỗ mở
    for k in (0, 1):
        f = lambda s, q, k=k: g.side(k, s, q)
        s0 = g.s_at_d(k, D_OPEN - UPPER_T, -T)
        end = facade_line(g, -0.3)
        s1 = max(g.s_at_d(k, fr.dd(p), -T) for p in (end[0] if k == 0 else end[-1],)) + 0.3
        hole = (OPEN_S[0], OPEN_S[1], Z0 - 0.01, Z0 + PORTAL_H)
        wall_run(walls, f, s0, s1, -T, 0.0, Z0, ZA, 'B1_SanhPanel', [hole])
        panel_joints(joints, f, s0 + 0.6, s1 - 0.3, -T, -1, Z0, ZA, rnd, [hole])
        for sa, sb in ((OPEN_S[0] - 0.16, OPEN_S[0]), (OPEN_S[1], OPEN_S[1] + 0.16)):     # má cổng sâu
            prism(walls, quad(f, sa, sb, -T - 0.18, 0.12), Z0, Z0 + PORTAL_H + 0.16, 'B1_SanhPaint')
        prism(walls, quad(f, OPEN_S[0] - 0.16, OPEN_S[1] + 0.16, -T - 0.18, 0.12), Z0 + PORTAL_H,
              Z0 + PORTAL_H + 0.16, 'B1_SanhPaint')
        prism(walls, quad(f, s0 - 0.05, s0 + 0.6, -T - 0.12, 0.3), Z0, ZC, 'B1_SanhPaint')    # cột vuông trắng
        PLAN_LABELS.append(('Cổng ra hành lang', f(sum(OPEN_S) / 2, -T - 1.2)))

    # mảng tường trên lỗ mở: mặt sảnh có ron ở hai bên, khe dọc ở giữa; mặt dưới xám đậm
    da, db = D_OPEN - UPPER_T, D_OPEN
    foot = [g.osm(0, db), g.osm(0, da), g.osm(1, da), g.osm(1, db)]
    prism(walls, foot, ZC, ZC + 0.02, 'B1_SanhSoffit')
    prism(walls, foot, ZC + 0.02, ZA, 'B1_SanhPanel')
    xw, xe = fr.xl(1, db), fr.xl(0, db)
    fu = lambda x, d: fr.w(x, d)
    span = xe - xw
    panel_joints(joints, fu, xw, xe, db, 1, ZC, ZA, rnd, zh=(Z0 + 4.4, Z0 + 4.6),
                 slots=(xw + span * 0.2, xe - span * 0.2))

    # lớp ốp phía trong mặt tiền: mép tường giữa các cụm kính, dải xám giữa hai băng kính, tường hai bên cửa
    P, N = g.arc['P'], g.arc['N']
    d0 = SHOP_WALL_D[0]
    for f0, f1 in g.lay['units']:
        margins, (ga, gb) = unit_split(f0, f1)
        for x0, x1 in margins:
            Ps, Ns = lerp_arc(P, N, x0, x1)
            curved_solid(walls, Ps, Ns, 0, len(Ps) - 1, Z0, GROUND_H, d0 - 0.03, d0, 'B1_SanhPanel')
        Ps, Ns = lerp_arc(P, N, ga, gb)
        curved_solid(walls, Ps, Ns, 0, len(Ps) - 1, BANK_Z[1], BANK_Z[2], d0 - 0.03, d0, 'B1_SanhBand')
        for i_, sgn in ((0, 1), (len(Ps) - 1, -1)):         # má trắng hai đầu ô kính (che mặt cắt tường kem)
            t = (Ps[min(i_ + 1, len(Ps) - 1)] - Ps[max(i_ - 1, 0)]).normalized() * sgn
            p, nn = Ps[i_], Ns[i_]
            prism(walls, [p + nn * d0, p + nn * (SHOP_WALL_D[0] + 0.48), p + nn * (SHOP_WALL_D[0] + 0.48) + t * 0.02,
                          p + nn * d0 + t * 0.02], Z0, GROUND_H, 'B1_SanhPanel')
    c0, u, n, half, zone = g.lay['c0'], g.lay['u'], g.lay['n'], g.lay['half'], g.lay['zone']
    fe = lambda s, d: c0 + u * s + n * d
    for sg in (-1, 1):
        sa, sb = sorted((sg * half, sg * (zone + 0.15)))
        prism(walls, quad(fe, sa, sb, REC - 1.03, REC - 1.0), Z0, GROUND_H, 'B1_SanhPanel')
        ja = sg * half
        prism(walls, quad(fe, ja - 0.03 if sg > 0 else ja, ja if sg > 0 else ja + 0.03, REC - 1.03, REC),
              Z0, GROUND_H, 'B1_SanhPanel')
    # dải trên đỉnh tầng 1 (4.5 m) nối mặt trong tầng 1 với mặt trong tường vành
    inner = facade_line(g, d0 - 0.03, REC - 1.03, REC)
    outer = facade_line(g, -0.28)
    band = clip(clip(inner + list(reversed(outer)), g.A, g.n_in[0]), g.A, g.n_in[1])
    prism(ceil, band, GROUND_H, GROUND_H + 0.12, 'B1_SanhPaint')
    # mặt trong tường vành, chừa ô cửa sổ vành (RING_WINDOWS) từ 5.9 m
    gz0 = level_top(1) + 1.4
    curved_solid(walls, P, N, 0, NS, GROUND_H + 0.12, gz0, -0.33, -0.3, 'B1_SanhPanel')
    cur = 0
    for f0, f1, _, _ in RING_WINDOWS:
        o0, o1 = int(round(f0 * NS)), int(round(f1 * NS))
        curved_solid(walls, P, N, cur, o0, gz0, ZA, -0.33, -0.3, 'B1_SanhPanel')
        cur = o1
    curved_solid(walls, P, N, cur, NS, gz0, ZA, -0.33, -0.3, 'B1_SanhPanel')

    # trần thông tầng (phủ cả nóc mảng tường trên lỗ mở)
    prism(ceil, fan_region(g, D_OPEN - UPPER_T, facade_line(g, -0.28)), ZA, ZA + 0.05, 'B1_SanhCeiling')
    for mb in (floor, pat, walls, joints, ceil):
        mb.build(coll)
    PLAN_LABELS.append(('Sảnh thông tầng', fr.w(X_C, 9.5)))


def build_reception(g, coll, ceil, lights, rnd):
    fr = g.fr
    rec = MB('B1_SanhReception')
    fl = MB('B1_SanhRecFloor')
    prism(fl, [g.A, g.osm(0, D_OPEN), g.osm(1, D_OPEN)], Z0 - 0.25, Z0, 'B1_SanhGranite', bottom=False)
    fl.build(coll)
    a_l, a_r = g.osm(1, D_OPEN - UPPER_T), g.osm(0, D_OPEN - UPPER_T)
    prism(ceil, [g.A, a_r, a_l], ZC, ZC + 0.08, 'B1_SanhSoffit')
    # tường logo: kính trắng bóng, khung vuông đồng hở góc, chữ HUST + tên trường
    x0, x1 = X_C - 2.5, X_C + 2.5
    prism(rec, [fr.w(x0, LOGO_D), fr.w(x1, LOGO_D), fr.w(x1, LOGO_D + 0.25), fr.w(x0, LOGO_D + 0.25)], Z0, ZC, 'B1_SanhLogo')
    face_d = LOGO_D + 0.25
    right, out = -fr.rt, fr.ax              # nhìn từ sảnh: chiều đọc là -rt (tây), mặt quay về +ax
    fx0, fx1, fz0, fz1 = X_C + 1.15, X_C - 0.85, Z0 + 1.15, Z0 + 3.05   # x giảm = sang phải người xem

    def bar(xa, xb, za, zb):
        xa, xb = sorted((xa, xb))
        prism(rec, [fr.w(xa, face_d), fr.w(xb, face_d), fr.w(xb, face_d + 0.015), fr.w(xa, face_d + 0.015)],
              za, zb, 'B1_SanhBronze')
    w = 0.035
    bar(fx0, fx0 - w, fz0, fz1)                         # cạnh trái
    bar(fx0, fx1, fz0, fz0 + w)                         # cạnh dưới
    bar(fx0, fx0 + (fx1 - fx0) * 0.78, fz1 - w, fz1)    # cạnh trên, hở góc phải
    bar(fx1 + w, fx1, fz0, fz0 + 0.55)                  # cạnh phải, đứt chỗ dòng chữ
    bar(fx1 + w, fx1, fz0 + 1.05, fz1 - 0.35)
    text_mesh(rec, 'HUST', 0.42, fr.w(fx0 - 0.22, face_d), right, out, Z0 + 2.35, 'B1_SanhBronze')
    text_mesh(rec, 'ĐẠI HỌC BÁCH KHOA HÀ NỘI', 0.15, fr.w(fx0 - 0.22, face_d), right, out, Z0 + 1.85, 'B1_SanhBronze')
    # quầy thẳng: thân trắng, mặt đá đen
    c0x, c1x = X_C - 2.4, X_C + 2.4
    prism(rec, [fr.w(c0x, COUNTER_D), fr.w(c1x, COUNTER_D), fr.w(c1x, COUNTER_D + 0.62), fr.w(c0x, COUNTER_D + 0.62)],
          Z0, Z0 + 1.05, 'B1_SanhCounter')
    prism(rec, [fr.w(c0x - 0.03, COUNTER_D - 0.03), fr.w(c1x + 0.03, COUNTER_D - 0.03),
                fr.w(c1x + 0.03, COUNTER_D + 0.65), fr.w(c0x - 0.03, COUNTER_D + 0.65)], Z0 + 1.05, Z0 + 1.1, 'B1_SanhDeskTop')
    rec.build(coll)
    PLAN_LABELS.append(('Quầy lễ tân', fr.w(X_C, COUNTER_D + 0.3)))
    PLAN_LABELS.append(('Tường logo HUST', fr.w(X_C, LOGO_D - 0.5)))

    # LED vạch toả tia trên trần xám đậm + đèn tròn
    focus = fr.w(X_C, D_OPEN + 4.5)
    tri = [g.A, a_r, a_l]
    for th in [-0.62 + 1.24 * i / 10 + rnd.uniform(-0.04, 0.04) for i in range(11)]:
        v = fr.rt * math.sin(th) - fr.ax * math.cos(th)
        t0 = rnd.uniform(5.0, 6.2)
        t1 = t0 + rnd.uniform(1.2, 2.4)
        p, q = focus + v * t0, focus + v * t1
        pts = [p.lerp(q, i / 12) for i in range(13)]
        pts = [x for x in pts if inside(tri, x) and fr.dd(x) > LOGO_D + 0.5 and fr.dd(x) < D_OPEN - UPPER_T - 0.15
               and all((x - g.A).dot(g.n_in[k]) > 0.25 for k in (0, 1))]
        if len(pts) > 2:
            seg_rect(lights, pts[0], pts[-1], 0.045, ZC - 0.012, ZC, 'B1_SanhLed')
    for x, d in ((X_C - 1.6, 2.0), (X_C + 1.6, 2.0), (X_C, 3.3)):
        cylinder(lights, fr.w(x, d), 0.07, ZC - 0.01, ZC, 'B1_Downlight', 12)


def door(mb, f, s0, s1, q, z0, z1, frame='B1_SanhAlu', leaf='B1_SanhFrosted', leaves=2, depth=0.12, fw=0.06):
    """Cửa đặt trong lỗ tường: khung quanh lỗ (q..q+depth), các cánh ở giữa bề dày."""
    prism(mb, quad(f, s0, s0 + fw, q, q + depth), z0, z1, frame)
    prism(mb, quad(f, s1 - fw, s1, q, q + depth), z0, z1, frame)
    prism(mb, quad(f, s0 + fw, s1 - fw, q, q + depth), z1 - fw, z1, frame)
    w = (s1 - s0 - 2 * fw) / leaves
    qm = q + depth / 2
    for i in range(leaves):
        a = s0 + fw + i * w
        b = a + w
        prism(mb, quad(f, a, b, qm - 0.015, qm + 0.015), z0, z1 - fw, leaf)
        for sa, sb in ((a, a + 0.05), (b - 0.05, b)):
            prism(mb, quad(f, sa, sb, qm - 0.025, qm + 0.025), z0, z1 - fw, frame)
        for za, zb in ((z0, z0 + 0.1), (z1 - fw - 0.06, z1 - fw)):
            prism(mb, quad(f, a, b, qm - 0.025, qm + 0.025), za, zb, frame)


def build_lobbies(g, coll, ceil, lights, rnd):
    hall, lifts, doors = MB('B1_SanhHall'), MB('B1_SanhLifts'), MB('B1_SanhDoors')
    marble = MB('B1_SanhMarble')
    floor = MB('B1_SanhLobbyFloor')
    for k in (0, 1):
        f = lambda s, q, k=k: g.side(k, s, q)
        name = 'Sảnh thang 3–4' if k == 0 else 'Sảnh thang 1–2'
        PLAN_LABELS.append((name, f(5.5, CORR / 2)))
        prism(floor, quad(f, 0.0, S_END + WALL, 0.0, CORR + WALL), Z0 - 0.25, Z0, 'B1_SanhGranite', bottom=False)
        prism(ceil, quad(f, 0.0, S_END, 0.0, CORR), ZC, ZC + 0.08, 'B1_SanhCeiling')
        qo = CORR                                     # mặt trong tường ngoài
        holes = [(sc - LIFT_W / 2, sc + LIFT_W / 2, Z0 - 0.01, Z0 + LIFT_H) for _, sc in LIFTS[k]]
        if k == 0:
            holes += [(7.0, 9.4, Z0 - 0.01, ZC - 0.3), (12.1, 13.7, Z0 - 0.01, Z0 + 2.5)]
        else:
            holes += [(0.4, 1.3, Z0 - 0.01, Z0 + 2.2), (8.8, 9.7, Z0 - 0.01, Z0 + 2.2),
                      (11.8, 12.9, Z0 + 1.0, Z0 + 2.6), (13.1, 14.2, Z0 + 1.0, Z0 + 2.6)]
        wall_run(hall, f, 0.0, S_END + WALL, qo, qo + WALL, Z0, ZC + 0.08, 'B1_SanhPaint', holes)
        # tường cuối (cắt sảnh thang), cửa đôi nhôm trắng
        fe = lambda t, w, k=k: g.side(k, S_END + w, t)
        wall_run(hall, fe, 0.0, CORR, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', [(1.0, 2.6, Z0 - 0.01, Z0 + 2.3)])
        door(doors, fe, 1.0, 2.6, -0.02, Z0, Z0 + 2.3)
        # ốp đá + thang máy
        m0, m1 = MARBLE_S[k]
        wall_run(marble, f, m0, m1, qo - 0.03, qo, Z0, ZC, 'B1_SanhMarble',
                 [h for h in holes if m0 <= h[0] <= m1])
        for label, sc in LIFTS[k]:
            a, b = sc - LIFT_W / 2, sc + LIFT_W / 2
            for sa, sb in ((a - 0.06, a), (b, b + 0.06)):
                prism(lifts, quad(f, sa, sb, qo - 0.05, qo + 0.13), Z0, Z0 + LIFT_H + 0.06, 'B1_Steel')
            prism(lifts, quad(f, a, b, qo - 0.05, qo + 0.13), Z0 + LIFT_H, Z0 + LIFT_H + 0.06, 'B1_Steel')
            prism(lifts, quad(f, a, b, qo + 0.13, qo + 0.16), Z0, Z0 + LIFT_H, 'B1_Steel')           # cánh inox
            prism(lifts, quad(f, sc - 0.004, sc + 0.004, qo + 0.12, qo + 0.13), Z0, Z0 + LIFT_H, 'B1_SanhJoint')
            prism(lifts, quad(f, a - 0.06, b + 0.06, qo - 0.06, qo + 0.13), Z0, Z0 + 0.008, 'B1_Steel')  # ngưỡng
            prism(lifts, quad(f, sc - 0.16, sc + 0.16, qo - 0.045, qo - 0.03), Z0 + LIFT_H + 0.28,
                  Z0 + LIFT_H + 0.46, 'B1_SanhScreen')                                                # bảng số tầng
            # nhìn vào tường thang (hướng +O): bên phải người xem là -dir (đông) / +dir (tây)
            text_mesh(lifts, label, 0.16, f(b + (0.24 if k == 0 else 0.12), qo - 0.03), g.dir[k] * (1 if k == 1 else -1),
                      -g.O[k], Z0 + LIFT_H - 0.3, 'B1_Steel')
        sm = sum(sc for _, sc in LIFTS[k]) / 2
        prism(lifts, quad(f, sm - 0.06, sm + 0.06, qo - 0.05, qo - 0.03), Z0 + 1.0, Z0 + 1.45, 'B1_Steel')  # nút gọi
        if k == 0:
            # vách kính cường lực cửa đôi, có dải mờ; phía sau là tiền phòng kín
            fv = f
            prism(hall, quad(fv, 7.0, 9.4, qo + WALL, qo + 2.4), Z0 - 0.25, Z0, 'B1_SanhGranite')
            prism(hall, quad(fv, 7.0, 9.4, qo + WALL, qo + 2.4), ZC - 0.3, ZC - 0.22, 'B1_SanhCeiling')
            for sa, sb, qa, qb in ((6.8, 7.0, qo, qo + 2.6), (9.4, 9.6, qo, qo + 2.6), (7.0, 9.4, qo + 2.4, qo + 2.6)):
                prism(hall, quad(fv, sa, sb, qa, qb), Z0, ZC - 0.22, 'B1_SanhPaint')
            for sa, sb in ((7.0, 7.55), (7.55, 8.2), (8.2, 8.85), (8.85, 9.4)):
                prism(doors, quad(fv, sa + 0.004, sb - 0.004, qo + 0.11, qo + 0.13), Z0 + 0.02, ZC - 0.32, 'B1_SanhGlass')
            for sa, sb in ((7.55, 8.2), (8.2, 8.85)):
                for za, zb in ((Z0 + 0.95, Z0 + 1.03), (Z0 + 1.2, Z0 + 1.24)):
                    prism(doors, quad(fv, sa + 0.02, sb - 0.02, qo + 0.105, qo + 0.11), za, zb, 'B1_SanhFrosted')
            for hs in (8.12, 8.28):
                prism(doors, quad(fv, hs - 0.012, hs + 0.012, qo + 0.03, qo + 0.06), Z0 + 0.9, Z0 + 1.9, 'B1_Steel')
            # cửa ra ngoài đối diện cổng má sâu phía đông
            door(doors, f, 12.1, 13.7, qo, Z0, Z0 + 2.5, 'B1_SanhSteelDark', 'B1_SanhDaylight')
        else:
            door(doors, f, 0.4, 1.3, qo, Z0, Z0 + 2.2, 'B1_SanhAlu', 'B1_SanhFrosted', 1)
            door(doors, f, 8.8, 9.7, qo, Z0, Z0 + 2.2, 'B1_SanhAluGrey', 'B1_SanhFrosted', 1)
            for sa, sb in ((11.8, 12.9), (13.1, 14.2)):         # cửa sổ lớp học khung xám, kính tối
                door(doors, f, sa, sb, qo, Z0 + 1.0, Z0 + 2.6, 'B1_SanhAluGrey', 'B1_GlassDark', 2)
        # LED vạch chéo + hai hàng đèn tròn
        s = 1.0
        while s < S_END - 1.0:
            ang = math.radians(rnd.uniform(25, 45)) * rnd.choice((-1, 1))
            dvec = g.dir[k] * math.cos(ang) + g.O[k] * math.sin(ang)
            c = f(s, CORR / 2 + rnd.uniform(-0.4, 0.4))
            ln = rnd.uniform(1.8, 2.6) / 2
            p, q = c - dvec * ln, c + dvec * ln
            for _ in range(8):     # co lại cho nằm gọn trong dải
                ok = all(0.25 < (x - g.A).dot(g.O[k]) < CORR - 0.25 for x in (p, q))
                if ok:
                    break
                p, q = p.lerp(c, 0.15), q.lerp(c, 0.15)
            seg_rect(lights, p, q, 0.045, ZC - 0.012, ZC, 'B1_SanhLed')
            s += rnd.uniform(1.8, 2.4)
        s = 0.9
        while s < S_END - 0.4:
            for qq in (0.8, CORR - 0.8):
                cylinder(lights, f(s, qq), 0.07, ZC - 0.01, ZC, 'B1_Downlight', 12)
            s += 1.7
    floor.build(coll)
    hall_ob = hall
    ob = marble.build(coll)
    if ob:
        box_uv(ob, 1.6)
    return hall_ob, lifts, doors


def build_stair_hall(g, coll, ceil, lights, hall, doors, rnd):
    r = g.rear
    stair = MB('B1_SanhStair')
    floor = MB('B1_SanhStairFloor')
    PLAN_LABELS.append(('Cầu thang', r(sum(STAIR_A1) / 2 + 1.0, 3.0)))
    PLAN_LABELS.append(('Cửa sau', r(1.0, REAR_B - 0.6)))
    prism(floor, quad(r, 0.0, REAR_A + WALL, 0.0, REAR_B + WALL), Z0 - 0.25, Z0, 'B1_SanhGranite', bottom=False)
    floor.build(coll)
    # f(a, b) = r ; tường tây (a = 0..WALL) dọc b, có 2 cửa đôi nhôm trắng nhìn từ sảnh thang 1–2
    fw_ = lambda t, w: r(w, t)
    wd = [(0.5, 1.8, Z0 - 0.01, Z0 + 2.3), (2.2, 3.5, Z0 - 0.01, Z0 + 2.3)]
    wall_run(hall, fw_, 0.0, REAR_B + WALL, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', wd)
    for sa, sb, _, _ in wd:
        door(doors, fw_, sa, sb, -0.02, Z0, Z0 + 2.3)
    # tường phía bắc (giáp cánh đông) dọc a ở b = 0..WALL
    fn = lambda s, w: r(s, w)
    prism(hall, quad(fn, CORR, REAR_A + WALL, 0.0, WALL), Z0, ZS, 'B1_SanhPaint')
    prism(hall, quad(fn, PASS_A, CORR + WALL, 0.0, WALL), ZC + 0.08, ZS, 'B1_SanhPaint')
    # tường đông
    prism(hall, quad(fn, REAR_A, REAR_A + WALL, WALL, REAR_B + WALL), Z0, ZS, 'B1_SanhPaint')
    # tường cuối: cửa sau (thép kính, ô thoáng hoa sắt) + cửa sổ trên chiếu nghỉ
    ff = lambda s, w: r(s, REAR_B + w)
    wall_run(hall, ff, WALL, PASS_A, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', [(0.4, 1.6, Z0 - 0.01, Z0 + 3.0)])
    wall_run(hall, ff, PASS_A, REAR_A, 0.0, WALL, Z0, ZS, 'B1_SanhPaint', [(2.4, 5.2, Z0 + 2.5, Z0 + 4.5)])
    door(doors, ff, 0.4, 1.6, 0.0, Z0, Z0 + 2.4, 'B1_SanhSteelDark', 'B1_SanhDaylight')
    prism(doors, quad(ff, 0.4, 1.6, 0.1, 0.12), Z0 + 2.4, Z0 + 3.0, 'B1_SanhDaylight')
    for k_ in range(9):                                         # hoa sắt ô thoáng
        sx = 0.4 + 1.2 * k_ / 8
        prism(doors, quad(ff, sx - 0.012, sx + 0.012, 0.06, 0.1), Z0 + 2.4, Z0 + 3.0, 'B1_SanhSteelDark')
    for zz in (Z0 + 2.4, Z0 + 2.7, Z0 + 2.97):
        prism(doors, quad(ff, 0.4, 1.6, 0.06, 0.1), zz, zz + 0.03, 'B1_SanhSteelDark')
    for i in range(4):                                          # nan chéo
        a0 = 0.4 + 0.3 * i
        seg = [ff(a0, 0.08), ff(a0 + 0.3, 0.08)]
        stair.face([(seg[0].x, seg[0].y, Z0 + 2.43), (seg[1].x, seg[1].y, Z0 + 2.67),
                    (seg[1].x, seg[1].y, Z0 + 2.7), (seg[0].x, seg[0].y, Z0 + 2.46)], 'B1_SanhSteelDark')
    door(doors, ff, 2.4, 5.2, 0.0, Z0 + 2.5, Z0 + 4.5, 'B1_SanhAluGrey', 'B1_SanhDaylight', 3)
    # tường giữa lối đi và cầu thang (dưới trần thấp chỉ có ở đoạn sau), phía trên là giếng thang
    prism(hall, quad(fn, PASS_A, PASS_A + 0.15, STAIR_B0 + 1.8, REAR_B), Z0, ZS, 'B1_SanhPaint')
    prism(hall, quad(fn, PASS_A, PASS_A + 0.15, WALL, STAIR_B0 + 1.8), ZC + 0.08, ZS, 'B1_SanhPaint')
    prism(hall, quad(fn, PASS_A - 0.25, PASS_A + 0.15, STAIR_B0 + 1.4, STAIR_B0 + 1.8), Z0, ZC, 'B1_SanhPaint')  # cột
    # trần: lối đi thấp, giếng thang cao
    prism(ceil, quad(fn, 0.0, PASS_A, 0.0, REAR_B), ZC, ZC + 0.08, 'B1_SanhCeiling')
    prism(ceil, quad(fn, PASS_A, REAR_A, 0.0, REAR_B), ZS, ZS + 0.1, 'B1_SanhCeiling')
    for bb in (1.2, 3.0, 4.8):
        cylinder(lights, r(0.95, bb), 0.07, ZC - 0.01, ZC, 'B1_Downlight', 12)
    for aa, bb in ((3.0, 2.0), (4.6, 4.2)):
        cylinder(lights, r(aa, bb), 0.08, ZS - 0.01, ZS, 'B1_Downlight', 12)

    # cầu thang chữ U: vế 1 lên về phía b lớn, chiếu nghỉ, vế 2 quay lại
    rise = STORY / 2 / N_RISE
    b1 = STAIR_B0 + N_RISE * TREAD
    a0, a1 = STAIR_A1
    for i in range(N_RISE):
        prism(stair, quad(fn, a0, a1, STAIR_B0 + i * TREAD, STAIR_B0 + (i + 1) * TREAD), Z0, Z0 + (i + 1) * rise,
              'B1_SanhStairStone')
    prism(stair, quad(fn, a0, STAIR_A2[1], b1, REAR_B), Z0, Z0 + STORY / 2, 'B1_SanhStairStone')     # chiếu nghỉ
    c0_, c1_ = STAIR_A2
    for i in range(N_RISE):
        top = Z0 + STORY / 2 + (i + 1) * rise
        prism(stair, quad(fn, c0_, c1_, b1 - (i + 1) * TREAD, b1 - i * TREAD), top - 0.4, top, 'B1_SanhStairStone')
    prism(stair, quad(fn, c0_, REAR_A, WALL, STAIR_B0), Z0 + STORY - 0.3, Z0 + STORY, 'B1_SanhStairStone')  # sàn tầng 2
    # tấm chắn trắng hoa văn dưới vế 2 (nhìn từ sảnh thang 3–4: bên trái chân thang)
    pb = STAIR_B0 - 0.04
    prism(stair, quad(fn, c0_ - 0.15, REAR_A, pb, STAIR_B0), Z0, Z0 + 1.25, 'B1_SanhPaint')
    nvec = -g.O[1]
    for zrow in (Z0 + 0.18, Z0 + 1.07):
        a = c0_ + 0.05
        while a < REAR_A - 0.1:
            c = fn(a, pb - 0.002)
            u = g.O[0] * 0.05
            stair.face([(c.x - u.x, c.y - u.y, zrow), (c.x, c.y, zrow - 0.05),
                        (c.x + u.x, c.y + u.y, zrow), (c.x, c.y, zrow + 0.05)], 'B1_SanhJoint', (nvec.x, nvec.y, 0))
            a += 0.13
    # lan can: song inox mỗi bậc, tay vịn gỗ dốc theo vế
    am = (a1 + c0_) / 2
    for i in range(N_RISE):
        for bb, z in ((STAIR_B0 + (i + 0.5) * TREAD, Z0 + (i + 1) * rise),
                      (b1 - (i + 0.5) * TREAD, Z0 + STORY / 2 + (i + 1) * rise)):
            prism(stair, quad(fn, am - 0.012, am + 0.012, bb - 0.012, bb + 0.012), z, z + 0.9, 'B1_Steel')
    for (bA, zA), (bB, zB) in (((STAIR_B0, Z0 + 0.9), (b1, Z0 + STORY / 2 + 0.9)),
                               ((b1, Z0 + STORY / 2 + 0.9), (STAIR_B0, Z0 + STORY + 0.9))):
        pa, pb2 = fn(am, bA), fn(am, bB)
        side = g.O[0] * 0.03
        q = [pa - side, pa + side, pb2 + side, pb2 - side]
        for za_off in (0.0,):
            zs = [zA, zA, zB, zB]
            stair.face([(q[i].x, q[i].y, zs[i] + 0.06) for i in range(4)], 'B1_SanhWood', (0, 0, 1))
            stair.face([(q[i].x, q[i].y, zs[i]) for i in range(4)], 'B1_SanhWood', (0, 0, -1))
            for i in range(4):
                j = (i + 1) % 4
                nrm = (q[i] + q[j]) / 2 - (pa + pb2) / 2
                stair.face([(q[i].x, q[i].y, zs[i]), (q[j].x, q[j].y, zs[j]),
                            (q[j].x, q[j].y, zs[j] + 0.06), (q[i].x, q[i].y, zs[i] + 0.06)], 'B1_SanhWood',
                           (nrm.x, nrm.y, 0))
    stair.build(coll)


def add_lights_and_cameras(g, coll):
    fr = g.fr

    def area(name, p, z, size, energy):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy, ld.shape, ld.size = energy, 'SQUARE', size
        ob = bpy.data.objects.new(name, ld)
        ob.location = (p.x, p.y, z)
        coll.objects.link(ob)

    area('B1_SanhLightAtrium0', fr.w(X_C, 7.5), ZA - 0.3, 6, 1800)
    area('B1_SanhLightAtrium1', fr.w(X_C, 11.5), ZA - 0.3, 6, 1800)
    area('B1_SanhLightRec', fr.w(X_C, 2.5), ZC - 0.2, 3, 300)
    for k in (0, 1):
        for s in (3.0, 8.0, 13.0):
            area(f'B1_SanhLightLobby{k}_{int(s)}', g.side(k, s, CORR / 2), ZC - 0.2, 2, 220)
    area('B1_SanhLightStair', g.rear(3.5, 3.0), ZS - 0.3, 3, 500)

    def cam(name, p, z, t, tz, lens):
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        ob = bpy.data.objects.new(name, cd)
        ob.location = (p.x, p.y, z)
        ob.rotation_euler = (Vector((t.x, t.y, tz)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(ob)

    e = Z0 + 1.6
    ent = g.lay['c0'] + g.lay['n'] * (REC - 1.6)
    cam('Cam_SanhEntry', ent, e, fr.w(X_C, 2.0), Z0 + 2.4, 18)                         # vào cửa, nhìn lễ tân
    cam('Cam_SanhHust', fr.w(X_C + 0.3, 10.5), e, fr.w(X_C, 2.0), Z0 + 3.0, 20)        # ảnh 910460593
    cam('Cam_SanhGlass', fr.w(4.5, 8.0), e, fr.w(-8.0, 13.5), Z0 + 2.4, 18)             # ảnh 907481651
    cam('Cam_SanhPortal', fr.w(3.0, 9.0), e, g.side(1, sum(OPEN_S) / 2, 0.0), Z0 + 2.6, 18)  # ảnh 912372993
    cam('Cam_SanhLifts34', g.side(0, 10.5, 1.0), e, g.side(0, -5.0, 2.2), Z0 + 1.9, 18)  # ảnh 907177005
    cam('Cam_SanhLifts12', g.side(1, 9.5, 1.0), e, g.side(1, -1.0, 2.6), Z0 + 1.6, 18)   # ảnh 906549668
    cam('Cam_SanhPlan', fr.w(X_C, 4.0), 62.0, fr.w(X_C, 4.0), 0.0, 30)


def build_sanh(parent, info, arc):
    """Dựng sảnh vào collection B1_Sanh (thứ được xuất ra web)."""
    PLAN_LABELS.clear()
    make_sanh_materials()
    fan = Fan(info[ENTRANCE_PART]['pts'])
    g = Geo(fan, arc)
    coll = collection(parent, 'B1_Sanh')
    rnd = random.Random(11)
    build_atrium(g, coll, rnd)
    ceil, lights = MB('B1_SanhHallCeiling'), MB('B1_SanhLights')
    build_reception(g, coll, ceil, lights, rnd)
    hall, lifts, doors = build_lobbies(g, coll, ceil, lights, rnd)
    build_stair_hall(g, coll, ceil, lights, hall, doors, rnd)
    for mb in (hall, lifts, doors, ceil, lights):
        mb.build(coll)
    add_lights_and_cameras(g, coll)
    return coll
