"""Sảnh B1 (tầng 1): model riêng, dựng vào B1_Sanh.blend, xuất ra web/public/models/buildings/b1/b1_sanh.glb.

Bố cục theo ảnh ref (C:/.../ref, 23 ảnh) và sketch mặt bằng user vẽ (lượt 2026-11-18):
  - Sảnh thông tầng: phần hình quạt từ lỗ mở (d = D_OPEN) tới mặt kính cong. Tường ốp tấm trắng ngà,
    ron đen: ron đứng không đều, ron ngang so le theo từng mảng. Mảng tường trên lỗ mở có khe dọc lõm.
    Hai cổng má sâu trên hai tường bên. Sàn granite xám đậm + hoa văn ô bậc thang đỏ/xám.
  - Sảnh sau (sau 2 cột trắng ở lỗ mở): hình chữ nhật, tường song song trục quạt, trần thấp ZC.
    Tường đông: thang 3 rồi 4 (bắc -> nam), cầu thang chữ U ở góc đông nam. Tường tây: thang 2 rồi 1, cửa đơn;
    góc bắc nối thẳng tường ngoài hành lang chéo tây.
    Giữa: quầy lễ tân chữ L + tường logo HUST, phòng 104 phía sau quầy (cửa sổ + cửa nhìn ra lối đi cửa sau).
    Tường sau: cửa sau (cuối lối đi giữa cầu thang và phòng 104). Góc tây nam là đa giác P2-P3-P4 (ảnh a6f71652)
    theo lưới 45° của cánh tây, đoạn P3-P4 có 2 cửa đôi.
    Trần xám đậm + LED toả tia từ lỗ mở tới trước quầy, phần còn lại trần trắng + đèn tròn.
  - Hai hành lang cánh nhà (dải dọc hai cạnh quạt, từ miệng ở góc sảnh sau tới S_END): miệng đông có vách
    kính cửa đôi, miệng tây để trống. Cổng má sâu từ sảnh thông tầng mở vào hai hành lang này.
Bỏ đồ rời (ghế, chậu cây, vách bình phong, TV) theo yêu cầu user.

Các hệ toạ độ 2D (đều ra toạ độ thế giới của tòa nhà, nên glb sảnh khớp glb vỏ ngoài):
  Frame (x, d) : x hướng đông, d dọc trục quạt tính từ đỉnh A (d < 0 là phía sau đỉnh). Sảnh sau dựng
                 thẳng trong hệ này (xem class Hall).
  side(k, s, q): dải dọc cạnh quạt k (0 = đông, 1 = tây); s dọc cạnh tính từ A, q ra ngoài tính từ mặt
                 ngoài tường quạt (đường OSM). Tường quạt nằm ở q ∈ [-T, 0]; hành lang ở q ∈ [0, CORR].
  Hall.r(a, b) : khung cầu thang góc đông nam; a theo hướng đông (a = REAR_A ở mặt trong tường đông),
                 b từ mép bắc giếng thang về phía sau (b = REAR_B ở mặt trong tường sau).
"""
import bisect
import math
import os
import random

import bpy
from mathutils import Vector

from .auditorium import fan_of
from .config import level_top
from .lobby import BANK_Z, LANDING_Z, NS, REC, SHOP_WALL_D, f1_layout, lerp_arc, unit_split
from .materials import image_material, principled
from .meshkit import MB, box_uv, collection, curved_solid, cylinder, prism

HERE = os.path.dirname(os.path.abspath(__file__))
MARBLE_PATH = os.path.join(os.path.dirname(HERE), 'textures', 'marble.jpg')

# ---------------------------------------------------------------- kích thước (m)
T = 0.35                    # dày tường quạt
Z0 = LANDING_Z              # cốt sàn trong nhà = chiếu nghỉ ngoài cửa (5 bậc)
ZC = Z0 + 3.6               # trần thấp: sảnh sau, hành lang
ZA = level_top(2) - 0.46    # trần thông tầng, dưới đáy sàn giảng đường (7.70) để không trùng mặt
ZS = Z0 + 6.6               # trần giếng cầu thang
D_OPEN = 4.3                # mặt lỗ mở từ sảnh thông tầng vào sảnh sau
UPPER_T = 0.6               # dày mảng tường trên lỗ mở
WALL = 0.25                 # tường trong
CORR = 3.6                  # rộng hành lang cánh nhà
S_END = 15.7                # hành lang cắt ở đây (sau cổng má sâu), tường + cửa
OPEN_S = (11.6, 14.1)       # cổng má sâu trên tường bên sảnh thông tầng (s)
PORTAL_H = 3.2
LIFT_W, LIFT_H = 1.1, 2.2
X_C = -0.6                  # đường giữa quầy lễ tân (đỉnh quạt lệch tây so với trục)
# sảnh sau, toạ độ Frame (x, d)
HALL_S = -9.6               # mặt trong tường sau
LIFTS_E = [('3', -0.6), ('4', -2.9)]     # tường đông: (số, d tâm cửa), bắc -> nam
MARBLE_D = (-4.1, 0.5)      # dải ốp đá quanh thang 3–4 (d)
WEST_CORR_DOOR = (9.6, 10.5)   # cửa trên tường ngoài hành lang chéo tây (s)
# phần tây sảnh sau theo lưới 45° của cánh tây, toạ độ side(1, s, q) (ảnh a6f71652, c763a1a8):
#   tường thang 1–2 nằm trên đường miệng hành lang chéo (s = s0) kéo dài, q từ CORR (góc lồi 90° với tường ngoài
#   hành lang) tới Q4; cạnh có 2 cửa đôi chạy song song hành lang ở q = Q4 từ P4 về P3; cạnh P3 -> P2 song song
#   tường thang, tới mặt tây phòng 104
LIFTS_W = [('2', CORR + 1.0), ('1', CORR + 3.3)]   # (số, q tâm cửa)
MARBLE_W = (CORR, CORR + 4.0)
DOOR_W1 = (CORR + 4.3, CORR + 5.2)    # cửa đơn trên tường thang, gần P4
P2_D = -7.1                 # d của P2 trên mặt tây phòng 104
P23 = 2.3                   # dài P2 -> P3
WEST_DOORS = [(1.2, 2.5), (4.6, 5.9)]   # 2 cửa đôi trên cạnh P3 -> P4 (s tính từ P3)
SOFFIT_D = -0.3             # trần xám đậm + LED toả tia từ lỗ mở tới đây, sau đó trần trắng
LOGO_D = -3.15              # mặt sau tường logo (= tường bắc phòng 104); mặt trước ở LOGO_D + 0.25
COUNTER_D = -1.52           # mép sau quầy; quầy sâu 0.62 -> mặt trước ở -0.9
R104_X = (-3.3, X_C)        # phòng 104 (mép ngoài hai tường tây / đông)
R104_OPEN = [('win', -4.85, -3.45), ('door', -6.35, -5.15), ('win', -7.45, -6.65), ('door1', -8.75, -7.85)]
R104_DOOR_W = (-4.4, -3.5)  # cửa đơn trắng trên tường tây phòng 104
# cầu thang chữ U góc đông nam, khung Hall.r(a, b)
REAR_A, REAR_B = 6.2, 5.6
STAIR_A1, STAIR_A2 = (2.4, 4.2), (4.4, 6.2)
STAIR_B0 = 0.8              # chân thang (b)
N_RISE, TREAD = 12, 0.28
STORY = level_top(1) - Z0   # sàn tầng 2 = 4.5
PASS_A = 2.2                # tường giữa lối đi cửa sau và cầu thang (a)
BACK_DOOR_A = (0.4, 1.6)    # cửa sau (a)

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

    # lớp ốp phía trong mặt tiền: mép tường giữa các cụm kính, dải xám giữa hai băng kính, tường hai bên cửa.
    # Tầng 1–2 ngoài nhà là một khối kem lõm cao 2 tầng (lobby.py), nên lớp ốp chạy thẳng tới trần thông tầng
    P, N = g.arc['P'], g.arc['N']
    d0 = SHOP_WALL_D[0]
    for unit in g.lay['units']:
        margins, (ga, gb) = unit_split(unit)
        for x0, x1 in margins:
            Ps, Ns = lerp_arc(P, N, x0, x1)
            curved_solid(walls, Ps, Ns, 0, len(Ps) - 1, Z0, ZA, d0 - 0.03, d0, 'B1_SanhPanel')
        Ps, Ns = lerp_arc(P, N, ga, gb)
        curved_solid(walls, Ps, Ns, 0, len(Ps) - 1, BANK_Z[1], BANK_Z[2], d0 - 0.03, d0, 'B1_SanhBand')
        for i_, sgn in ((0, 1), (len(Ps) - 1, -1)):         # má trắng hai đầu ô kính (che mặt cắt tường kem)
            t = (Ps[min(i_ + 1, len(Ps) - 1)] - Ps[max(i_ - 1, 0)]).normalized() * sgn
            p, nn = Ps[i_], Ns[i_]
            prism(walls, [p + nn * d0, p + nn * (SHOP_WALL_D[0] + 0.48), p + nn * (SHOP_WALL_D[0] + 0.48) + t * 0.02,
                          p + nn * d0 + t * 0.02], Z0, ZA, 'B1_SanhPanel')
    c0, u, n, half, zone = g.lay['c0'], g.lay['u'], g.lay['n'], g.lay['half'], g.lay['zone']
    fe = lambda s, d: c0 + u * s + n * d
    for sg in (-1, 1):
        sa, sb = sorted((sg * half, sg * (zone + 0.15)))
        prism(walls, quad(fe, sa, sb, REC - 1.03, REC - 1.0), Z0, ZA, 'B1_SanhPanel')
        ja = sg * half
        prism(walls, quad(fe, ja - 0.03 if sg > 0 else ja, ja if sg > 0 else ja + 0.03, REC - 1.03, REC),
              Z0, ZA, 'B1_SanhPanel')
    # (vành tròn trắng nằm trên trần thông tầng, tầng 3–4: không có mặt nào của nó nhìn thấy từ trong sảnh)

    # trần thông tầng (phủ cả nóc mảng tường trên lỗ mở), dừng ngay sau mặt kính như sàn: phần ngoài kính là
    # dải trần ngoài trời dưới vành (Lobby_F1_Soffit, vỏ ngoài)
    prism(ceil, fan_region(g, D_OPEN - UPPER_T, facade_line(g, SHOP_WALL_D[0] + 0.48, REC - 1.0, REC)),
          ZA, ZA + 0.05, 'B1_SanhCeiling')
    for mb in (floor, pat, walls, joints, ceil):
        mb.build(coll)
    PLAN_LABELS.append(('Sảnh thông tầng', fr.w(X_C, 9.5)))


class Hall:
    """Sảnh sau: chữ nhật thẳng trong Frame. Mép bắc = lỗ mở giữa 2 cột + 2 miệng hành lang (vuông góc cạnh quạt).
    Tường đông/tây đặt ở mặt trong tường ngoài hành lang tại miệng, nên góc sảnh khớp góc hành lang."""

    def __init__(self, g):
        fr = g.fr
        self.s0 = [g.s_at_d(k, D_OPEN - UPPER_T, -T) for k in (0, 1)]      # s của cột trắng = miệng hành lang
        self.mouth_in = [g.side(k, self.s0[k], 0.0) for k in (0, 1)]       # đầu miệng trên đường OSM
        self.corner = [g.side(k, self.s0[k], CORR) for k in (0, 1)]        # góc sảnh (mặt trong tường)
        self.corner_out = [g.side(k, self.s0[k], CORR + WALL) for k in (0, 1)]
        self.XE, self.XW = fr.loc(self.corner[0])[0], fr.loc(self.corner[1])[0]
        self.dE, self.dW = fr.dd(self.corner[0]), fr.dd(self.corner[1])
        self.XB = self.XE - REAR_A                  # gốc a của khung cầu thang
        self.XS = self.XB + PASS_A                  # mép tây giếng thang
        self.D_WELL = HALL_S + REAR_B               # mép bắc giếng thang
        w = fr.w
        self.fe = lambda s, q: w(self.XE + q, s)    # tường đông: s = d, q vào trong tường
        self.fw = lambda s, q: w(self.XW - q, s)    # tường tây
        self.fb = lambda s, q: w(s, HALL_S - q)     # tường sau: s = x
        self.r = lambda a, b: w(self.XB + a, HALL_S + REAR_B - b)
        self.ua, self.ub = fr.rt.copy(), -fr.ax
        # phần tây theo lưới cánh tây: P2 trên mặt tây phòng 104, P3 = (sP3, Q4), P4 = (s0, Q4) trên tường thang
        self.g, self.fr, self.O1, self.D1 = g, fr, g.O[1].copy(), g.dir[1].copy()
        self.P2 = w(R104_X[0], P2_D)
        self.sP3 = (self.P2 - g.A).dot(self.D1)
        self.Q4 = (self.P2 - g.A).dot(self.O1) + P23
        self.P3 = g.side(1, self.sP3, self.Q4)
        self.P4 = g.side(1, self.s0[1], self.Q4)
        self.L34 = self.s0[1] - self.sP3
        m0, m1 = self.mouth_in[1], self.mouth_in[0]
        t = (R104_X[0] - fr.loc(m0)[0]) / (fr.loc(m1)[0] - fr.loc(m0)[0])
        self.top = m0.lerp(m1, t)                  # mép bắc sảnh tại mặt tây phòng 104

    def west_poly(self, off=0.0):
        """Phần tây sảnh sau (lồi): mép bắc -> miệng hành lang -> tường thang -> P4 -> P3 -> P2 (off: lấn chân tường cửa)."""
        g = self.g
        return [self.top, self.mouth_in[1], g.side(1, self.s0[1], self.Q4 + off),
                g.side(1, self.sP3, self.Q4 + off), self.P2]

    def east_of_104(self, poly):
        return clip(poly, self.fr.w(R104_X[0], 0.0), self.fr.rt)


def lift_door(mb, f, sc, qo, label, lab_s, right, out):
    """Một cửa thang máy trong lỗ tường f(s, q) (q vào trong tường, mặt tường ở qo); số tầng ghi ở lab_s."""
    a, b = sc - LIFT_W / 2, sc + LIFT_W / 2
    for sa, sb in ((a - 0.06, a), (b, b + 0.06)):
        prism(mb, quad(f, sa, sb, qo - 0.05, qo + 0.13), Z0, Z0 + LIFT_H + 0.06, 'B1_Steel')
    prism(mb, quad(f, a, b, qo - 0.05, qo + 0.13), Z0 + LIFT_H, Z0 + LIFT_H + 0.06, 'B1_Steel')
    prism(mb, quad(f, a, b, qo + 0.13, qo + 0.16), Z0, Z0 + LIFT_H, 'B1_Steel')                # cánh inox
    prism(mb, quad(f, sc - 0.004, sc + 0.004, qo + 0.12, qo + 0.13), Z0, Z0 + LIFT_H, 'B1_SanhJoint')
    prism(mb, quad(f, a - 0.06, b + 0.06, qo - 0.06, qo + 0.13), Z0, Z0 + 0.008, 'B1_Steel')    # ngưỡng
    prism(mb, quad(f, sc - 0.16, sc + 0.16, qo - 0.045, qo - 0.03), Z0 + LIFT_H + 0.28,
          Z0 + LIFT_H + 0.46, 'B1_SanhScreen')                                                 # bảng số tầng
    text_mesh(mb, label, 0.16, f(lab_s, qo - 0.03), right, out, Z0 + LIFT_H - 0.3, 'B1_Steel', align='CENTER')


def lift_wall(lifts, marble, f, pairs, right, out, mrange):
    """Hai thang cạnh nhau trên một tường: cửa, số ghi ở khoảng giữa hai cửa, nút gọi, ốp đá."""
    (l0, s0), (l1, s1) = sorted(pairs, key=lambda p: p[1])
    gap = LIFT_W / 2 + 0.2
    lift_door(lifts, f, s0, 0.0, l0, s0 + gap, right, out)
    lift_door(lifts, f, s1, 0.0, l1, s1 - gap, right, out)
    sm = (s0 + s1) / 2
    prism(lifts, quad(f, sm - 0.06, sm + 0.06, -0.05, -0.03), Z0 + 1.0, Z0 + 1.45, 'B1_Steel')       # nút gọi
    holes = [(sc - LIFT_W / 2, sc + LIFT_W / 2, Z0 - 0.01, Z0 + LIFT_H) for _, sc in pairs]
    wall_run(marble, f, mrange[0], mrange[1], -0.03, 0.0, Z0, ZC, 'B1_SanhMarble', holes)


def build_hall(g, h, coll, ceil, lights, hall, lifts, doors, rnd):
    fr = g.fr
    floor, marble = MB('B1_SanhHallFloor'), MB('B1_SanhMarble')
    da = D_OPEN - UPPER_T
    # sàn: hình thang giữa hai đường OSM (tới lỗ mở) + lục giác sảnh; hành lang nối ở miệng (s = s0)
    x_out = [fr.loc(p)[0] for p in h.corner_out]
    prism(floor, [g.osm(0, D_OPEN), g.osm(1, D_OPEN), h.mouth_in[1], h.mouth_in[0]], Z0 - 0.25, Z0,
          'B1_SanhGranite', bottom=False)
    hexf = [h.mouth_in[0], h.corner_out[0], fr.w(x_out[0], HALL_S - WALL), fr.w(x_out[1], HALL_S - WALL),
            h.corner_out[1], h.mouth_in[1]]
    for poly in (h.east_of_104(hexf), h.west_poly(0.12)):
        prism(floor, poly, Z0 - 0.25, Z0, 'B1_SanhGranite', bottom=False)
    floor.build(coll)

    # trần: xám đậm từ lỗ mở tới SOFFIT_D, còn lại trắng (chừa giếng thang, cắt góc tây nam)
    hexa = [h.mouth_in[0], h.corner[0], fr.w(h.XE, HALL_S), fr.w(h.XW, HALL_S), h.corner[1], h.mouth_in[1]]
    ps = fr.w(0.0, SOFFIT_D)
    ea, wp = h.east_of_104(hexa), h.west_poly()
    soffit = [clip(ea, ps, fr.ax), clip(wp, ps, fr.ax)]
    pw = fr.w(h.XS, h.D_WELL)
    we = clip(ea, ps, -fr.ax)
    white = [clip(we, pw, -fr.rt), clip(clip(we, pw, fr.rt), pw, fr.ax), clip(wp, ps, -fr.ax)]
    prism(ceil, [g.osm(0, da), g.osm(1, da), h.mouth_in[1], h.mouth_in[0]], ZC, ZC + 0.08, 'B1_SanhSoffit')
    for poly in soffit:
        prism(ceil, poly, ZC, ZC + 0.08, 'B1_SanhSoffit')
    for poly in white:
        prism(ceil, poly, ZC, ZC + 0.08, 'B1_SanhCeiling')

    def inset(poly, p, m):
        return all(inside(poly, p + o) for o in (fr.rt * m, -fr.rt * m, fr.ax * m, -fr.ax * m))

    # LED vạch toả tia từ lỗ mở (ảnh ff958ece)
    focus = fr.w(X_C, D_OPEN + 4.5)
    for th in [-0.62 + 1.24 * i / 10 + rnd.uniform(-0.04, 0.04) for i in range(11)]:
        v = fr.rt * math.sin(th) - fr.ax * math.cos(th)
        t0 = rnd.uniform(5.2, 6.2)
        p, q = focus + v * t0, focus + v * (t0 + rnd.uniform(3.0, 5.5))
        pts = [p.lerp(q, i / 24) for i in range(25)]
        pts = [x for x in pts if any(inset(sp, x, 0.3) for sp in soffit) and fr.dd(x) < da - 0.15]
        if len(pts) > 2:
            seg_rect(lights, pts[0], pts[-1], 0.045, ZC - 0.012, ZC, 'B1_SanhLed')
    # đèn tròn trên trần trắng (không đặt trong phòng 104)
    x = min(fr.loc(p)[0] for p in wp) + 0.9
    while x < h.XE - 0.4:
        d = HALL_S + 0.9
        while d < SOFFIT_D - 0.3:
            p = fr.w(x, d)
            in_room = R104_X[0] - 0.2 < x < R104_X[1] + 0.2 and d < LOGO_D + 0.4
            if not in_room and any(inset(poly, p, 0.35) for poly in white):
                cylinder(lights, p, 0.07, ZC - 0.01, ZC, 'B1_Downlight', 12)
            d += 1.7
        x += 1.7

    # tường đông: 2 thang, đoạn cạnh giếng thang cao tới trần giếng
    holes_e = [(sc - LIFT_W / 2, sc + LIFT_W / 2, Z0 - 0.01, Z0 + LIFT_H) for _, sc in LIFTS_E]
    wall_run(hall, h.fe, HALL_S, h.D_WELL, 0.0, WALL, Z0, ZS, 'B1_SanhPaint')
    wall_run(hall, h.fe, h.D_WELL, h.dE, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', holes_e)
    # nhìn vào tường đông (hướng đông): tay phải là phía nam (-ax); tường tây ngược lại
    lift_wall(lifts, marble, h.fe, LIFTS_E, -fr.ax, -fr.rt, MARBLE_D)
    # tường tây = mặt đông khối thang 1–2, từ P4 tới góc bắc: cửa đơn + 2 thang, ốp đá tới sát góc
    # tường thang 1–2: trên đường miệng hành lang chéo kéo dài (s = s0), vuông góc tường ngoài hành lang
    # -> góc lồi 90° ở q = CORR (ảnh c763a1a8). Nhìn vào tường (hướng dir[1]): tay phải = (D1.y, -D1.x)
    s0w = h.s0[1]
    fl = lambda t, w: g.side(1, s0w + w, t)
    holes_w = [(sc - LIFT_W / 2, sc + LIFT_W / 2, Z0 - 0.01, Z0 + LIFT_H) for _, sc in LIFTS_W]
    holes_w.append((DOOR_W1[0], DOOR_W1[1], Z0 - 0.01, Z0 + 2.2))
    wall_run(hall, fl, CORR, h.Q4 + WALL, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', holes_w)
    lift_wall(lifts, marble, fl, LIFTS_W, Vector((h.D1.y, -h.D1.x)), -h.D1, MARBLE_W)
    door(doors, fl, DOOR_W1[0], DOOR_W1[1], -0.02, Z0, Z0 + 2.2, leaves=1)
    ob = marble.build(coll)
    if ob:
        box_uv(ob, 1.6)
    # góc tây nam: P2 -> P3 (tây nam), P3 -> P4 (tây bắc) có 2 cửa đôi nhôm trắng; tường nằm phía ngoài đường nối
    f23 = lambda s, q: h.P2 + h.O1 * s - h.D1 * q
    prism(hall, quad(f23, 0.0, P23, 0.0, WALL), Z0, ZC + 0.08, 'B1_SanhPaint')
    f34 = lambda s, q: h.P3 + h.D1 * s + h.O1 * q
    wall_run(hall, f34, -WALL, h.L34 + WALL, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint',
             [(a, b, Z0 - 0.01, Z0 + 2.3) for a, b in WEST_DOORS])
    for a, b in WEST_DOORS:
        door(doors, f34, a, b, -0.02, Z0, Z0 + 2.3)
    # tường sau (từ phòng 104 sang đông): cửa sau; đoạn giếng thang cao tới trần giếng, cửa sổ chiếu nghỉ
    bd = (h.XB + BACK_DOOR_A[0], h.XB + BACK_DOOR_A[1])
    wall_run(hall, h.fb, R104_X[0], h.XS, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', [(bd[0], bd[1], Z0 - 0.01, Z0 + 3.0)])
    wall_run(hall, h.fb, h.XS, h.XE + WALL, 0.0, WALL, Z0, ZS, 'B1_SanhPaint',
             [(h.XB + 2.4, h.XB + 5.2, Z0 + 2.5, Z0 + 4.5)])

    # phòng 104: tường đông nhìn ra lối đi cửa sau (cửa sổ lớn, cửa đôi, cửa sổ nhỏ, cửa hẹp), tường tây 1 cửa
    x0r, x1r = R104_X
    f_e = lambda s, q: fr.w(x1r - q, s)
    f_w = lambda s, q: fr.w(x0r + q, s)
    holes = []
    for kind, sa, sb in R104_OPEN:
        holes.append((sa, sb, Z0 + 1.2, Z0 + 2.3) if kind == 'win' else (sa, sb, Z0 - 0.01, Z0 + 2.3))
    wall_run(hall, f_e, HALL_S, LOGO_D, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', holes)
    for kind, sa, sb in R104_OPEN:
        if kind == 'win':
            door(doors, f_e, sa, sb, 0.0, Z0 + 1.2, Z0 + 2.3, 'B1_SanhAluGrey', 'B1_GlassDark', 2)
        else:
            door(doors, f_e, sa, sb, 0.0, Z0, Z0 + 2.3, 'B1_SanhAluGrey', 'B1_SanhFrosted', 2 if kind == 'door' else 1)
    wall_run(hall, f_w, HALL_S, LOGO_D, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint',
             [(R104_DOOR_W[0], R104_DOOR_W[1], Z0 - 0.01, Z0 + 2.2)])
    door(doors, f_w, R104_DOOR_W[0], R104_DOOR_W[1], 0.0, Z0, Z0 + 2.2, leaves=1)

    # vách kính cửa đôi chắn miệng hành lang đông (ảnh ff958ece, 5041f095); miệng tây để trống
    fm = lambda t, w, s0=h.s0[0]: g.side(0, s0 + w, t)
    t0, t1 = 0.3, CORR
    prism(hall, quad(fm, t0, t1, -0.08, 0.08), ZC - 0.3, ZC + 0.08, 'B1_SanhPaint')
    side_w = (t1 - t0 - 1.6) / 2
    e = [t0, t0 + side_w, t0 + side_w + 0.8, t1 - side_w, t1]
    for a, b in zip(e, e[1:]):
        prism(doors, quad(fm, a + 0.004, b - 0.004, -0.01, 0.01), Z0 + 0.02, ZC - 0.32, 'B1_SanhGlass')
    for a, b in ((e[1], e[2]), (e[2], e[3])):
        for za, zb in ((Z0 + 0.69, Z0 + 0.72), (Z0 + 0.8, Z0 + 1.4), (Z0 + 1.48, Z0 + 1.51)):
            prism(doors, quad(fm, a + 0.02, b - 0.02, -0.014, -0.01), za, zb, 'B1_SanhFrosted')
    for hs in (e[2] - 0.08, e[2] + 0.08):
        prism(doors, quad(fm, hs - 0.012, hs + 0.012, -0.06, -0.03), Z0 + 0.9, Z0 + 1.9, 'B1_Steel')

    PLAN_LABELS.append(('Thang máy 3–4', fr.w(h.XE - 1.3, -1.75)))
    PLAN_LABELS.append(('Thang máy 1–2', g.side(1, h.s0[1] - 1.3, (CORR + h.Q4) / 2)))
    PLAN_LABELS.append(('Phòng 104', fr.w((x0r + x1r) / 2, -6.5)))


def build_reception(g, h, coll):
    fr = g.fr
    rec = MB('B1_SanhReception')
    # tường logo: kính trắng bóng, khung vuông đồng hở góc, chữ HUST + tên trường
    x0, x1 = R104_X[0], X_C + 2.5
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

    # quầy chữ L: thân trắng, mặt đá đen; đoạn quay ở đầu đông (nét móc trong sketch)
    def box(xa, xb, d0, d1, z0, z1, mat):
        prism(rec, [fr.w(xa, d0), fr.w(xb, d0), fr.w(xb, d1), fr.w(xa, d1)], z0, z1, mat)
    c0x, c1x = X_C - 2.4, X_C + 2.4
    front = COUNTER_D + 0.62
    box(c0x, c1x, COUNTER_D, front, Z0, Z0 + 1.05, 'B1_SanhCounter')
    box(c1x - 0.62, c1x, COUNTER_D - 0.8, COUNTER_D, Z0, Z0 + 1.05, 'B1_SanhCounter')
    box(c0x - 0.03, c1x + 0.03, COUNTER_D - 0.03, front + 0.03, Z0 + 1.05, Z0 + 1.1, 'B1_SanhDeskTop')
    box(c1x - 0.65, c1x + 0.03, COUNTER_D - 0.83, COUNTER_D - 0.03, Z0 + 1.05, Z0 + 1.1, 'B1_SanhDeskTop')
    rec.build(coll)
    PLAN_LABELS.append(('Quầy lễ tân', fr.w(X_C, COUNTER_D + 0.3)))
    PLAN_LABELS.append(('Logo HUST', fr.w(X_C + 1.2, LOGO_D + 0.75)))


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


def build_corridors(g, h, coll, ceil, lights, hall, doors, rnd):
    """Hai hành lang cánh nhà dọc cạnh quạt, từ miệng ở góc sảnh sau (s = s0) tới S_END."""
    floor = MB('B1_SanhCorrFloor')
    for k in (0, 1):
        f = lambda s, q, k=k: g.side(k, s, q)
        s0 = h.s0[k]
        PLAN_LABELS.append(('Hành lang cánh ' + ('đông' if k == 0 else 'tây'), f(s0 + 3.0, CORR / 2)))
        sw = s0
        prism(floor, quad(f, sw, S_END + WALL, 0.0, CORR + WALL), Z0 - 0.25, Z0, 'B1_SanhGranite', bottom=False)
        prism(ceil, quad(f, s0, S_END, 0.0, CORR), ZC, ZC + 0.08, 'B1_SanhCeiling')
        qo = CORR                                     # mặt trong tường ngoài
        cd = WEST_CORR_DOOR
        if k == 0:
            holes = [(12.1, 13.7, Z0 - 0.01, Z0 + 2.5)]
        else:
            holes = [(cd[0], cd[1], Z0 - 0.01, Z0 + 2.2), (11.8, 12.9, Z0 + 1.0, Z0 + 2.6), (13.1, 14.2, Z0 + 1.0, Z0 + 2.6)]
        wall_run(hall, f, sw, S_END + WALL, qo, qo + WALL, Z0, ZC + 0.08, 'B1_SanhPaint', holes)
        # tường cuối (cắt hành lang), cửa đôi nhôm trắng
        fe = lambda t, w, k=k: g.side(k, S_END + w, t)
        wall_run(hall, fe, 0.0, CORR, 0.0, WALL, Z0, ZC + 0.08, 'B1_SanhPaint', [(1.0, 2.6, Z0 - 0.01, Z0 + 2.3)])
        door(doors, fe, 1.0, 2.6, -0.02, Z0, Z0 + 2.3)
        if k == 0:
            door(doors, f, 12.1, 13.7, qo, Z0, Z0 + 2.5, 'B1_SanhSteelDark', 'B1_SanhDaylight')  # cửa ra ngoài
        else:
            door(doors, f, cd[0], cd[1], qo, Z0, Z0 + 2.2, 'B1_SanhAluGrey', 'B1_SanhFrosted', 1)
            for sa, sb in ((11.8, 12.9), (13.1, 14.2)):         # cửa sổ lớp học khung xám, kính tối
                door(doors, f, sa, sb, qo, Z0 + 1.0, Z0 + 2.6, 'B1_SanhAluGrey', 'B1_GlassDark', 2)
        # LED vạch chéo + hai hàng đèn tròn
        s = s0 + 1.0
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
        s = s0 + 0.9
        while s < S_END - 0.4:
            for qq in (0.8, CORR - 0.8):
                cylinder(lights, f(s, qq), 0.07, ZC - 0.01, ZC, 'B1_Downlight', 12)
            s += 1.7
    floor.build(coll)


def build_stair(g, h, coll, ceil, lights, hall, doors):
    """Cầu thang chữ U góc đông nam sảnh sau: vế 1 lên về phía tường sau, chiếu nghỉ, vế 2 quay lại sát tường đông.
    Tấm chắn hoa văn dưới vế 2, cột ở chân thang phía lối đi, cửa sau + cửa sổ chiếu nghỉ trên tường sau."""
    r, ua, ub = h.r, h.ua, h.ub
    stair = MB('B1_SanhStair')
    PLAN_LABELS.append(('Cầu thang', r(sum(STAIR_A1) / 2 + 1.0, 3.0)))
    PLAN_LABELS.append(('Cửa sau', r(sum(BACK_DOOR_A) / 2, REAR_B - 0.6)))
    fn = r
    # giếng thang: mép bắc + tường phía lối đi (trên trần thấp), đoạn sau kín tới sàn, cột ở chân thang
    prism(hall, quad(fn, PASS_A, REAR_A, 0.0, WALL), ZC + 0.08, ZS, 'B1_SanhPaint')
    prism(hall, quad(fn, PASS_A, PASS_A + 0.15, STAIR_B0 + 1.8, REAR_B), Z0, ZS, 'B1_SanhPaint')
    prism(hall, quad(fn, PASS_A, PASS_A + 0.15, WALL, STAIR_B0 + 1.8), ZC + 0.08, ZS, 'B1_SanhPaint')
    prism(hall, quad(fn, PASS_A - 0.25, PASS_A + 0.15, STAIR_B0 + 1.4, STAIR_B0 + 1.8), Z0, ZC, 'B1_SanhPaint')  # cột
    prism(ceil, quad(fn, PASS_A, REAR_A, 0.0, REAR_B), ZS, ZS + 0.1, 'B1_SanhCeiling')
    for aa, bb in ((3.5, 2.0), (5.1, 4.2)):
        cylinder(lights, r(aa, bb), 0.08, ZS - 0.01, ZS, 'B1_Downlight', 12)

    # cửa sau (thép kính, ô thoáng hoa sắt) + cửa sổ trên chiếu nghỉ, trong lỗ tường sau (build_hall)
    ff = lambda s, w: r(s, REAR_B + w)
    a0d, a1d = BACK_DOOR_A
    door(doors, ff, a0d, a1d, 0.0, Z0, Z0 + 2.4, 'B1_SanhSteelDark', 'B1_SanhDaylight')
    prism(doors, quad(ff, a0d, a1d, 0.1, 0.12), Z0 + 2.4, Z0 + 3.0, 'B1_SanhDaylight')
    for k_ in range(9):                                         # hoa sắt ô thoáng
        sx = a0d + (a1d - a0d) * k_ / 8
        prism(doors, quad(ff, sx - 0.012, sx + 0.012, 0.06, 0.1), Z0 + 2.4, Z0 + 3.0, 'B1_SanhSteelDark')
    for zz in (Z0 + 2.4, Z0 + 2.7, Z0 + 2.97):
        prism(doors, quad(ff, a0d, a1d, 0.06, 0.1), zz, zz + 0.03, 'B1_SanhSteelDark')
    for i in range(4):                                          # nan chéo
        a0 = a0d + (a1d - a0d) / 4 * i
        seg = [ff(a0, 0.08), ff(a0 + (a1d - a0d) / 4, 0.08)]
        stair.face([(seg[0].x, seg[0].y, Z0 + 2.43), (seg[1].x, seg[1].y, Z0 + 2.67),
                    (seg[1].x, seg[1].y, Z0 + 2.7), (seg[0].x, seg[0].y, Z0 + 2.46)], 'B1_SanhSteelDark')
    door(doors, ff, 2.4, 5.2, 0.0, Z0 + 2.5, Z0 + 4.5, 'B1_SanhAluGrey', 'B1_SanhDaylight', 3)

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
    # bản thang vế 2: mặt dưới phẳng nghiêng (che các bậc treo), chạm góc dưới của từng bậc
    zs0, zs1 = Z0 + STORY / 2 - 0.4, Z0 + STORY - 0.4
    p00, p10, p11, p01 = fn(c0_, b1), fn(c1_, b1), fn(c1_, STAIR_B0), fn(c0_, STAIR_B0)
    stair.face([(p00.x, p00.y, zs0), (p10.x, p10.y, zs0), (p11.x, p11.y, zs1), (p01.x, p01.y, zs1)],
               'B1_SanhStairStone', (0, 0, -1))
    for pa_, pb_, sg in ((p00, p01, -1), (p10, p11, 1)):
        stair.face([(pa_.x, pa_.y, zs0), (pb_.x, pb_.y, zs1), (pb_.x, pb_.y, zs1 + 0.4), (pa_.x, pa_.y, zs0 + 0.4)],
                   'B1_SanhStairStone', (ua.x * sg, ua.y * sg, 0))
    # tấm chắn trắng hoa văn dưới vế 2 (nhìn từ thang 3–4: bên trái chân thang)
    pb = STAIR_B0 - 0.04
    prism(stair, quad(fn, c0_ - 0.15, REAR_A, pb, STAIR_B0), Z0, Z0 + 1.25, 'B1_SanhPaint')
    nvec = -ub
    for zrow in (Z0 + 0.18, Z0 + 1.07):
        a = c0_ + 0.05
        while a < REAR_A - 0.1:
            c = fn(a, pb - 0.002)
            u = ua * 0.05
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
        side = ua * 0.03
        q = [pa - side, pa + side, pb2 + side, pb2 - side]
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


def add_lights_and_cameras(g, h, coll):
    fr = g.fr

    def area(name, p, z, size, energy):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy, ld.shape, ld.size = energy, 'SQUARE', size
        ob = bpy.data.objects.new(name, ld)
        ob.location = (p.x, p.y, z)
        coll.objects.link(ob)

    area('B1_SanhLightAtrium0', fr.w(X_C, 7.5), ZA - 0.3, 6, 1800)
    area('B1_SanhLightAtrium1', fr.w(X_C, 11.5), ZA - 0.3, 6, 1800)
    area('B1_SanhLightRec', fr.w(X_C, 1.5), ZC - 0.2, 3, 300)
    area('B1_SanhLightHallE', fr.w(h.XE - 2.5, -2.0), ZC - 0.2, 2.5, 260)
    pw_ = (h.P2 + h.P3 + h.P4 + h.corner[1]) / 4
    area('B1_SanhLightHallW', pw_, ZC - 0.2, 3, 320)
    area('B1_SanhLightPass', fr.w((X_C + h.XS) / 2, -6.5), ZC - 0.2, 2, 200)
    for k in (0, 1):
        for s in (h.s0[k] + 2.5, h.s0[k] + 7.0):
            area(f'B1_SanhLightCorr{k}_{int(s)}', g.side(k, s, CORR / 2), ZC - 0.2, 2, 220)
    area('B1_SanhLightStair', h.r(4.3, 3.0), ZS - 0.3, 3, 500)

    def cam(name, p, z, t, tz, lens):
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        ob = bpy.data.objects.new(name, cd)
        ob.location = (p.x, p.y, z)
        ob.rotation_euler = (Vector((t.x, t.y, tz)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(ob)

    e = Z0 + 1.6
    ent = g.lay['c0'] + g.lay['n'] * (REC - 1.6)
    desk = fr.w(X_C, COUNTER_D)
    cam('Cam_SanhEntry', ent, e, desk, Z0 + 2.0, 18)                                     # vào cửa, nhìn lễ tân
    cam('Cam_SanhHust', fr.w(X_C + 0.3, 10.5), e, desk, Z0 + 2.6, 20)                   # ảnh 910460593, 267a3d5e
    cam('Cam_SanhGlass', fr.w(4.5, 8.0), e, fr.w(-8.0, 13.5), Z0 + 2.4, 18)             # ảnh 907481651
    cam('Cam_SanhPortal', fr.w(3.0, 9.0), e, g.side(1, sum(OPEN_S) / 2, 0.0), Z0 + 2.6, 18)  # ảnh 912372993
    cam('Cam_SanhHall', fr.w(X_C + 0.5, -0.3), e, fr.w(X_C + 0.5, 12.0), Z0 + 2.0, 16)  # ảnh ff958ece
    # đứng sát vách kính miệng hành lang đông, nhìn dọc tường thang 3–4 (ảnh 907177005, 5041f095)
    cam('Cam_SanhLifts34', g.side(0, h.s0[0] - 0.5, CORR * 0.35), e, fr.w(h.XE + 0.2, -8.5), Z0 + 1.8, 14)
    cam('Cam_SanhLifts12', fr.w(R104_X[0] - 0.3, 0.6), e, (h.P3 + h.P4) / 2, Z0 + 1.4, 14)  # ảnh a6f71652, 906549668
    cam('Cam_SanhBack', fr.w(X_C + 1.2, -3.6), e, fr.w(X_C + 1.4, -12.0), Z0 + 1.6, 16)  # ảnh d85e56b0
    # trước thang 2 nhìn dọc hành lang chéo tây, góc lồi 90° khối thang bên trái (ảnh c763a1a8)
    cam('Cam_SanhCorrW', g.side(1, h.s0[1] - 2.2, CORR - 0.9), e, g.side(1, S_END, CORR * 0.6), Z0 + 1.5, 14)
    cam('Cam_SanhPlan', fr.w(X_C, 1.0), 62.0, fr.w(X_C, 1.0), 0.0, 30)


def build_sanh(parent, info, arc):
    """Dựng sảnh vào collection B1_Sanh (thứ được xuất ra web)."""
    PLAN_LABELS.clear()
    make_sanh_materials()
    fan = fan_of(info)
    g = Geo(fan, arc)
    h = Hall(g)
    coll = collection(parent, 'B1_Sanh')
    rnd = random.Random(11)
    build_atrium(g, coll, rnd)
    ceil, lights = MB('B1_SanhHallCeiling'), MB('B1_SanhLights')
    hall, lifts, doors = MB('B1_SanhHall'), MB('B1_SanhLifts'), MB('B1_SanhDoors')
    build_hall(g, h, coll, ceil, lights, hall, lifts, doors, rnd)
    build_reception(g, h, coll)
    build_corridors(g, h, coll, ceil, lights, hall, doors, rnd)
    build_stair(g, h, coll, ceil, lights, hall, doors)
    for mb in (hall, lifts, doors, ceil, lights):
        mb.build(coll)
    add_lights_and_cameras(g, h, coll)
    print(f'Sảnh sau: XE={h.XE:.2f} XW={h.XW:.2f} góc d={h.dE:.2f}/{h.dW:.2f} chân thang d={HALL_S + REAR_B - STAIR_B0:.2f}')
    p3, p4 = g.fr.loc(h.P3), g.fr.loc(h.P4)
    print(f'Phần tây: P3=({p3[0]:.2f}, {g.fr.dd(h.P3):.2f}) P4=({p4[0]:.2f}, {g.fr.dd(h.P4):.2f}) '
          f'cạnh P3P4={h.L34:.2f} m, P2P3={P23:.2f} m, tường thang={h.Q4 - CORR:.2f} m')
    return coll
