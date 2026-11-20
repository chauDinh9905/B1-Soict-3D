"""Office wings: one object per block of the layout (facades + its roof slab)."""
import math
import random

from .config import ENTRANCE_PART, BAND_D, BAY_W, PARAPET, PIL_D, PIL_W, level_top
from .geom import point_in_poly, right_normal
from .materials import GLASS_POOL
from mathutils import Vector
from .meshkit import MB, V3, box_along, quad_along


def strip_window(mb, rnd, a, u, n, s0, s1, z0, z1, panes, transom):
    """Recessed aluminium strip window: glass on the wall line, mullions/transom in front."""
    fw = 0.07
    pw = (s1 - s0) / panes
    zt = z1 - (z1 - z0) * transom
    for i in range(panes):
        p0, p1 = s0 + i * pw, s0 + (i + 1) * pw
        quad_along(mb, a, u, n, p0, p1, z0, zt, 0.0, rnd.choice(GLASS_POOL))
        quad_along(mb, a, u, n, p0, p1, zt, z1, 0.0, rnd.choice(GLASS_POOL))
    for i in range(panes + 1):
        sx = s0 + i * pw
        box_along(mb, a, u, n, max(s0, sx - fw / 2), min(s1, sx + fw / 2), z0, z1, 0.0, 0.08, 'B1_Frame')
    box_along(mb, a, u, n, s0, s1, zt - 0.03, zt + 0.03, 0.0, 0.08, 'B1_Frame')
    box_along(mb, a, u, n, s0, s1, z0, z0 + fw, 0.0, 0.08, 'B1_Frame')
    box_along(mb, a, u, n, s0, s1, z1 - fw, z1, 0.0, 0.08, 'B1_Frame')


CLUSTER_PANEL_W = 0.5
CLUSTER_ALL = True   # every bay facade (front and back) uses the cluster window; False = only faces towards Cam_Ref
CLUSTER_FACING = Vector((-0.54, 0.84))   # direction from the building towards Cam_Ref / the courtyard photos
CLUSTER_MIN_DOT = 0.05


def cluster_window_ops(quad, box, s0, s1, z0, z1, transom=0.26):
    """Sketch 'mỗi cụm cửa sổ': 3 identical windows (full-width transom strip over 2 panes)
    separated by 2 narrow panels whose outline is as thin as the window frames. Every pane uses the same glass material.

    Geometry is emitted through two callables so the same design works on a straight wall and on the curved lobby ring:
      quad(s0, s1, z0, z1, d, mat)        flat panel at depth d
      box(s0, s1, z0, z1, d0, d1, mat)    solid between depths d0..d1
    s runs along the wall, d is measured outwards from the glass plane."""
    pw = CLUSTER_PANEL_W
    ww = (s1 - s0 - 2 * pw) / 3
    zt = z1 - (z1 - z0) * transom
    fw = 0.06
    for k in range(3):
        w0 = s0 + k * (ww + pw)
        w1 = w0 + ww
        wm = (w0 + w1) / 2
        quad(w0, w1, z0, z1, 0.0, 'B1_GlassCluster')
        box(w0, w1, zt - 0.03, zt + 0.03, 0.0, 0.08, 'B1_Frame')
        box(wm - fw / 2, wm + fw / 2, z0, zt, 0.0, 0.08, 'B1_Frame')
        for sx in ((w0,) if k == 0 else ()) + ((w1,) if k == 2 else ()):  # inner edges are the panel frames
            box(max(s0, sx - fw / 2), min(s1, sx + fw / 2), z0, z1, 0.0, 0.08, 'B1_Frame')
        box(w0, w1, z0, z0 + fw, 0.0, 0.08, 'B1_Frame')
        box(w0, w1, z1 - fw, z1, 0.0, 0.08, 'B1_Frame')
        if k < 2:  # narrow panel between windows; its outline is as thin as the window frames
            p0, p1 = w1, w1 + pw
            quad(p0, p1, z0, z1, 0.0, 'B1_GlassCluster')
            box(p0, p0 + fw, z0, z1, 0.0, 0.08, 'B1_Frame')
            box(p1 - fw, p1, z0, z1, 0.0, 0.08, 'B1_Frame')
            box(p0, p1, z0, z0 + fw, 0.0, 0.08, 'B1_Frame')
            box(p0, p1, z1 - fw, z1, 0.0, 0.08, 'B1_Frame')
            box(p0, p1, zt - 0.03, zt + 0.03, 0.0, 0.08, 'B1_Frame')  # transom runs across


def cluster_window(mb, a, u, n, s0, s1, z0, z1, transom=0.26):
    """cluster_window_ops on a straight wall from a along u, outward normal n."""
    cluster_window_ops(lambda *q: quad_along(mb, a, u, n, *q),
                       lambda *b: box_along(mb, a, u, n, *b), s0, s1, z0, z1, transom)


def floors_in(levels, z0, z1):
    for lv in range(1, levels + 1):
        fb, ft = level_top(lv - 1), level_top(lv)
        if fb >= z0 - 0.01 and ft <= z1 + 0.01:
            yield lv, fb, ft


def facade_bays(mb, rnd, a, b, n, levels, z0, z1, ext, cluster=False, parapet=True):
    L = (b - a).length
    u = (b - a) / L
    nb = max(1, round(L / BAY_W))
    bw = L / nb
    for lv, fb, ft in floors_in(levels, z0, z1):
        oz0, oz1 = fb + 0.95, ft - 0.35
        ground = lv == 1
        for j in range(nb):
            if cluster:
                cluster_window(mb, a, u, n, j * bw + PIL_W / 2, (j + 1) * bw - PIL_W / 2, oz0, oz1,
                               0.3 if ground else 0.26)
            else:
                strip_window(mb, rnd, a, u, n, j * bw + PIL_W / 2, (j + 1) * bw - PIL_W / 2, oz0, oz1,
                             5 if ground else 6, 0.3 if ground else 0.26)
    slabs = [level_top(lv) for lv in range(0, levels)]
    for s in slabs:
        if s >= z0 - 0.01 and s < z1 - 0.5:
            box_along(mb, a, u, n, -ext[0](BAND_D), L + ext[1](BAND_D),
                      max(z0, s - 0.35), min(z1, s + 0.95), 0.0, BAND_D, 'B1_Wall')
    top = z1 + PARAPET if parapet else z1
    box_along(mb, a, u, n, -ext[0](BAND_D), L + ext[1](BAND_D), z1 - 0.35, top, -0.25, BAND_D, 'B1_Wall')
    for j in range(nb + 1):
        s0 = -ext[0](PIL_D) if j == 0 else j * bw - PIL_W / 2
        s1 = L + ext[1](PIL_D) if j == nb else j * bw + PIL_W / 2
        box_along(mb, a, u, n, s0, s1, z0, top + (0.05 if parapet else 0.0), 0.0, PIL_D, 'B1_Wall')


def facade_end(mb, rnd, a, b, n, levels, z0, z1, ext, win_t=0.5, windows=True, parapet=True):
    L = (b - a).length
    u = (b - a) / L
    ww = 1.3
    wc = L * win_t
    if not windows or L < 3:
        box_along(mb, a, u, n, -ext[0](BAND_D), L + ext[1](BAND_D), z0, z1, 0.0, BAND_D, 'B1_Wall')
    else:
        box_along(mb, a, u, n, -ext[0](BAND_D), wc - ww / 2, z0, z1, 0.0, BAND_D, 'B1_Wall')
        box_along(mb, a, u, n, wc + ww / 2, L + ext[1](BAND_D), z0, z1, 0.0, BAND_D, 'B1_Wall')
        cur = z0
        for lv, fb, ft in floors_in(levels, z0, z1):
            oz0 = fb + (1.3 if lv == 1 else 1.0)
            oz1 = oz0 + (2.0 if lv == 1 else 1.6)
            box_along(mb, a, u, n, wc - ww / 2, wc + ww / 2, cur, oz0, 0.0, BAND_D, 'B1_Wall')
            quad_along(mb, a, u, n, wc - ww / 2, wc + ww / 2, oz0, oz1, 0.12, rnd.choice(GLASS_POOL))
            box_along(mb, a, u, n, wc - ww / 2, wc + ww / 2, oz0 + 0.62 * (oz1 - oz0) - 0.03,
                      oz0 + 0.62 * (oz1 - oz0) + 0.03, 0.12, 0.2, 'B1_Frame')
            box_along(mb, a, u, n, wc - 0.03, wc + 0.03, oz0, oz0 + 0.62 * (oz1 - oz0), 0.12, 0.2, 'B1_Frame')
            box_along(mb, a, u, n, wc - ww / 2 - 0.1, wc + ww / 2 + 0.1, oz0 - 0.08, oz0, BAND_D, BAND_D + 0.08, 'B1_Wall')
            cur = oz1
        box_along(mb, a, u, n, wc - ww / 2, wc + ww / 2, cur, z1, 0.0, BAND_D, 'B1_Wall')
    for lv in range(1, levels):
        s = level_top(lv)
        if z0 + 0.3 < s < z1 - 0.3:
            box_along(mb, a, u, n, -ext[0](BAND_D), L + ext[1](BAND_D), s - 0.06, s + 0.06, BAND_D, BAND_D + 0.04, 'B1_Wall')
    if parapet:
        box_along(mb, a, u, n, -ext[0](BAND_D), L + ext[1](BAND_D), z1, z1 + PARAPET, -0.25, BAND_D, 'B1_Wall')


def corner_ext(prev_pt, pt, next_pt):
    d0, d1 = (pt - prev_pt).normalized(), (next_pt - pt).normalized()
    cross = d0.x * d1.y - d0.y * d1.x
    ang = abs(math.atan2(cross, d0.dot(d1)))
    if cross <= 1e-6:
        return lambda d: 0.0
    return lambda d: min(d * math.tan(ang / 2), 2 * d)


def wing_names(info):
    """B1_Wing_<levels>F[_A/_B], lettered west to east when a height occurs more than once."""
    names = {}
    wings = [p for p in info.values() if p['id'] != ENTRANCE_PART]
    for lv in sorted({p['levels'] for p in wings}, reverse=True):
        same = sorted((p for p in wings if p['levels'] == lv), key=lambda p: sum(q.x for q in p['pts']))
        for k, p in enumerate(same):
            names[p['id']] = f'B1_Wing_{lv:02d}F' + (f'_{chr(65 + k)}' if len(same) > 1 else '')
    return names


def build_wings(info, coll, lay):
    """info: lay.build_parts(); lay (the layout module) also names the edges getting the gable treatment
    (END_EDGES, window column at gable_win_t), the sign (SIGN_EDGE) and a plain wall without parapet
    (PLAIN_EDGES, the corner bays behind the stair tower)."""
    by_edge = {}
    for p in info.values():
        for i in range(len(p['refs'])):
            by_edge.setdefault(frozenset((p['refs'][i], p['refs'][(i + 1) % len(p['refs'])])), []).append(p)

    rnd = random.Random(7)
    lobby = info[ENTRANCE_PART]['pts'] if ENTRANCE_PART in info else None
    for wid, name in wing_names(info).items():
        p = info[wid]
        mb = MB(name)
        mb.face([V3(q, p['h']) for q in p['pts']], 'B1_Roof', (0, 0, 1))
        refs, pts, n_pts = p['refs'], p['pts'], len(p['pts'])
        for i in range(n_pts):
            ra, rb = refs[i], refs[(i + 1) % n_pts]
            key = frozenset((ra, rb))
            z0 = max([0.0] + [o['h'] for o in by_edge[key] if o is not p])
            if z0 >= p['h'] - 0.01:
                continue
            a, b = pts[i], pts[(i + 1) % n_pts]
            n = right_normal(b - a)
            ext = (corner_ext(pts[i - 1], a, b), corner_ext(a, b, pts[(i + 2) % n_pts]))
            if key in lay.END_EDGES:
                win_t = lay.gable_win_t(ra, rb)
                facade_end(mb, rnd, a, b, n, p['levels'], z0, p['h'], ext, win_t=win_t)
                if key == lay.SIGN_EDGE:   # sign over the window column: start the edge at that end
                    p['sign'] = (a, b, n) if win_t < 0.5 else (b, a, n)
            elif key in lay.PLAIN_EDGES:
                facade_end(mb, rnd, a, b, n, p['levels'], z0, p['h'], ext, windows=False, parapet=False)
            elif (b - a).length < 3:
                facade_end(mb, rnd, a, b, n, p['levels'], z0, p['h'], ext, windows=False)
            else:
                cl = CLUSTER_ALL or Vector((n.x, n.y)).dot(CLUSTER_FACING) > CLUSTER_MIN_DOT
                # the V's inner faces rise from the lobby roof: no parapet there (user: stray walls on the roof)
                inner = lobby is not None and point_in_poly((a + b) / 2 + n * 0.5, lobby)
                facade_bays(mb, rnd, a, b, n, p['levels'], z0, p['h'], ext, cluster=cl, parapet=not inner)
            p.setdefault('edges', {})[key] = (a, b, n)
        mb.build(coll)
