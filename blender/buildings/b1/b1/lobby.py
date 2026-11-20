"""Main lobby (sảnh chính): the curved block in the inner corner of the V.

Pieces (each its own object):
  B1_Lobby_F1    floors 1-2, cream walls    - recessed curved glazing, square piers, entrance frame + doors,
                                              soffit (only the outdoor strip under the ring: the lobby interior
                                              is its own model, sanh.py -> B1_Sanh.blend)
  B1_Lobby_Ring  floors 3-4, white          - curved ring wall with cornice/parapet, 3 gridded window groups, roof
  B1_Lobby_Porch porte-cochere              - straight canopy with chamfered fascia, 2 steel columns, 2 steps

Layout reference: plan coordinates along the arc use P[i] (wall line) and N[i] (outward normal);
the straight porch/entrance pieces use the tangent frame (c0, u, n) at the middle of the arc,
s = distance along u, d = distance in front of the tangent plane.
"""
import math

from mathutils import Vector

from . import layout
from .config import level_top
from .meshkit import (MB, N3, V3, box_along, collection, curved_solid, cylinder, prism, quad_along,
                      ribbon)

NS = 96            # arc samples (~0.26 m each)
REC = -2.2         # cream base glazing set back behind the ring wall line
# user: the lobby has 4 storeys - floors 1-2 are the cream base (recessed under the ring, photos 116c/047b),
# floors 3-4 the white ring
BASE_LV = 2
BASE_H = level_top(BASE_LV)

# porch / entrance, in the mid-arc tangent frame
# user: the entrance block was squeezed; widen it step by step (the shopfronts either side shrink to match).
# Scales the width of the door frame's cream flanks and the canopy/columns; 1.0 = the first version
ENTRY_SCALE = 1.25
DOOR_BAYS = 5      # sketch: 5 bays x 3 rows, double doors in bays 2 and 4
DOOR_BAY_W = 2.6   # user: the glazed entrance frame reaches well past the two porch columns (seen from the front)
DOOR_ROWS = (0.78, 3.2, 5.65, BASE_H)
FLANK_W = 2.1 * ENTRY_SCALE      # cream wall either side of the entrance frame
CANOPY_HALF = 4.8 * ENTRY_SCALE
CANOPY_FRONT = 6.0
CANOPY_TOP, CANOPY_BOT = BASE_H - 0.05, BASE_H - 0.7   # canopy tucked under the ring
CANOPY_SLOPE = 0.3  # fascia leans out towards the top
COL_S, COL_D, COL_R = 2.8 * ENTRY_SCALE, 4.4, 0.38
STEP_H = 0.15
N_STEPS = 5         # user: the porch stair has 5 risers
STEP_TREAD = 0.35
LANDING_Z = N_STEPS * STEP_H
ENTRY_F = 0.5     # user: the front of the lobby is symmetric - entrance + canopy on the arc middle
# ring windows (from, to, columns) as fractions of the arc from its west end, symmetric about the middle (user sketch)
RING_WINDOWS = [(0.06, 0.25, 5), (0.29, 0.71, 9), (0.75, 0.94, 5)]
RING_GLASS = 'B1_GlassCluster'
RING_TRANSOM = 0.26   # row split of each storey = transom height of the wings' cluster windows, so the lines run through


def arc_frame():
    """The layout's lobby arc (west end to east end, covering LOBBY_BAYS bays of each arm), sampled NS times."""
    P, cen, R = layout.lobby_arc(NS)
    apex = layout.CORNER.copy()
    N = []
    for p in P:
        r = (p - cen).normalized()
        N.append(r if r.dot(p - apex) > 0 else -r)
    return {'P': P, 'N': N, 'apex': apex, 'center': cen, 'R': R, 'HE': level_top(layout.LOBBY_LEVELS),
            'entry': tangent_frame(P, N)}


def tangent_frame(P, N, f=ENTRY_F):
    im = int(round(f * NS))
    n = N[im].copy()
    u = Vector((-n.y, n.x))
    if u.dot(P[-1] - P[0]) < 0:
        u = -u
    return P[im].copy(), u, n


def tangent_at(P, i):
    return (P[min(i + 1, NS)] - P[max(i - 1, 0)]).normalized()


def square_post(mb, P, N, i, d, half, z0, z1, mat):
    t = tangent_at(P, i)
    c = P[i] + N[i] * d
    prism(mb, [c - t * half - N[i] * half, c + t * half - N[i] * half,
               c + t * half + N[i] * half, c - t * half + N[i] * half], z0, z1, mat)


# --------------------------------------------------------------------------- ground floor (cream)

UNIT_W = 4.4          # target width of one shopfront unit (m), stretched to fit its segment
UNIT_WALL = (0.237, 0.179)   # cream wall share of a unit on its outer / inner side (sketch proportions)
# lower glass = floor 1, cream band = floor-2 slab, upper glass = floor 2; levels match the wings' windows/bands
BANK_Z = (0.15, level_top(1) - 0.35, level_top(1) + 0.95, BASE_H - 0.35)
SHOP_WALL_D = (-1.3, -0.45)   # cream wall thickness range
SHOP_GLASS_D = -0.8


def seg_len(P, i0, i1):
    return sum((P[i + 1] - P[i]).length for i in range(i0, i1))


def lerp_arc(P, N, f0, f1, step=0.5):
    """Sub-sampled copy of the arc between fractional indices f0 and f1 (inclusive)."""
    n = max(1, math.ceil((f1 - f0) / step))
    Ps, Ns = [], []
    for k in range(n + 1):
        f = f0 + (f1 - f0) * k / n
        i = min(int(f), NS - 1)
        t = f - i
        Ps.append(P[i].lerp(P[i + 1], t))
        Ns.append(N[i].lerp(N[i + 1], t).normalized())
    return Ps, Ns


def unit_split(unit):
    """One merged shopfront (f0, f1, walls, panes): its two cream wall margins and the glazed span between,
    all as fractional arc indices."""
    f0, f1, walls, _ = unit
    a, b = f0 + walls[0], f1 - walls[1]
    return [(f0, a), (b, f1)], (a, b)


def f1_layout(P, N):
    """Floor 1-2 layout of the curved front: tangent frame at the entrance, half widths of the door frame and
    of the straight entrance block, and one merged shopfront per side. Shared by the exterior (build_f1) and
    the lobby's inner lining (sanh.py)."""
    c0, u, n = tangent_frame(P, N)
    s_of = [(p - c0).dot(u) for p in P]
    half = DOOR_BAYS * DOOR_BAY_W / 2
    zone = half + FLANK_W                              # half width of the straight entrance block
    i_lo = max(i for i in range(NS + 1) if s_of[i] <= -zone + 0.4)
    i_hi = min(i for i in range(NS + 1) if s_of[i] >= zone - 0.4)
    # user: the units on a side are merged into one, so a side gets 5 panes per merged unit and keeps the
    # outer/inner wall widths of a single unit, mirrored east/west
    units = []
    for seg0, seg1, west in ((0, i_lo, True), (i_hi, NS, False)):
        k = max(1, round(seg_len(P, seg0, seg1) / UNIT_W))
        uw = (seg1 - seg0) / k
        outer, inner = UNIT_WALL[0] * uw, UNIT_WALL[1] * uw
        units.append((seg0, seg1, (outer, inner) if west else (inner, outer), 5 * k))
    return {'c0': c0, 'u': u, 'n': n, 'zone': zone, 'half': half, 'i_lo': i_lo, 'i_hi': i_hi, 'units': units}


def shop_unit(gl, wl, P, N, unit):
    """Shopfront between fractional arc indices f0..f1; walls = cream margin widths (index units) at f0 / f1."""
    margins, (a, b) = unit_split(unit)
    panes = unit[3]
    d0, d1 = SHOP_WALL_D
    for x0, x1 in margins:                                # cream wall margins
        Ps, Ns = lerp_arc(P, N, x0, x1)
        curved_solid(wl, Ps, Ns, 0, len(Ps) - 1, 0.0, BASE_H, d0, d1, 'B1_WallCream')
    Ps, Ns = lerp_arc(P, N, a, b)
    last = len(Ps) - 1
    zl0, zl1, zu0, zu1 = BANK_Z
    curved_solid(wl, Ps, Ns, 0, last, zl1, zu0, d0, d1, 'B1_WallCream')       # cream band between banks
    curved_solid(wl, Ps, Ns, 0, last, 0.0, zl0, d0, d1, 'B1_WallCream')       # plinth under the lower bank
    curved_solid(wl, Ps, Ns, 0, last, zu1, BASE_H, d0, d1, 'B1_WallCream')    # head over the upper bank
    # (no dark backing behind the glass: the lobby interior is its own model and must show through)
    for z0, z1 in ((zl0, zl1), (zu0, zu1)):
        ribbon(gl, Ps, Ns, 0, last, SHOP_GLASS_D, z0, z1, 'B1_GlassLobby', smooth=False)
        curved_solid(gl, Ps, Ns, 0, last, z0, z0 + 0.07, SHOP_GLASS_D, SHOP_GLASS_D + 0.14, 'B1_FrameDark')
        curved_solid(gl, Ps, Ns, 0, last, z1 - 0.07, z1, SHOP_GLASS_D, SHOP_GLASS_D + 0.14, 'B1_FrameDark')
    for k in range(panes + 1):
        f = a + (b - a) * k / panes
        Pm, Nm = lerp_arc(P, N, f, f + 1e-3, step=1.0)
        t = (Pm[-1] - Pm[0]).normalized()
        c = Pm[0] + Nm[0] * SHOP_GLASS_D
        hw = 0.05 if 0 < k < panes else 0.09
        n0 = Nm[0]
        for z0, z1 in ((zl0, zl1), (zu0, zu1)):
            prism(gl, [c - t * hw, c + t * hw, c + t * hw + n0 * 0.14, c - t * hw + n0 * 0.14], z0, z1, 'B1_FrameDark')



def build_f1(arc, coll):
    P, N = arc['P'], arc['N']
    lay = f1_layout(P, N)
    c0, u, n, zone = lay['c0'], lay['u'], lay['n'], lay['zone']

    # one shopfront either side of the entrance block (user sketch): cream wall | upper glass bank over a
    # cream band over a lower glass bank | cream wall (see f1_layout)
    gl = MB('Lobby_F1_Glass')
    wl = MB('Lobby_F1_Walls')
    for unit in lay['units']:
        shop_unit(gl, wl, P, N, unit)
    gl.build(coll)
    wl.build(coll)

    # cream square piers under the ring, cream end walls, cream walls flanking the entrance
    pr = MB('Lobby_F1_EntranceWalls')
    for i, j in ((0, 1), (NS, NS - 1)):
        t = (P[j] - P[i]).normalized()
        prism(pr, [P[i], P[i] + N[i] * (REC - 0.3), P[i] + N[i] * (REC - 0.3) + t * 0.6, P[i] + t * 0.6],
              0.0, BASE_H, 'B1_WallCream')
    half = DOOR_BAYS * DOOR_BAY_W / 2
    R = arc['R']
    front = lambda s: math.sqrt(R * R - s * s) - R - 0.45      # 0.45 behind the arc, like the shopfront walls
    pt = lambda s, d: c0 + u * s + n * d
    for sg in (-1, 1):   # user: these must stay inside the ring's circle, so the front face follows the arc
        s0, s1 = sorted((sg * half, sg * (zone + 0.15)))
        prism(pr, [pt(s0, REC - 1.0), pt(s1, REC - 1.0), pt(s1, front(s1)), pt(s0, front(s0))],
              0.0, BASE_H, 'B1_WallCream')
    pr.build(coll)

    # entrance frame: 5 bays x 3 rows, double doors in bays 2 and 4 (sketch sảnh.png, right)
    ef = MB('Lobby_F1_EntranceFrame')
    dr = MB('Lobby_F1_Doors')      # double-door leaves: own object, the web lets you walk through (noCollide)
    d_gl = REC + 0.04
    z_rows = DOOR_ROWS
    for b in range(DOOR_BAYS):
        s0, s1 = -half + b * DOOR_BAY_W, -half + (b + 1) * DOOR_BAY_W
        door = b in (1, 3)
        for r in range(len(z_rows) - 1):
            quad_along(dr if door and r == 0 else ef, c0, u, n, s0, s1, z_rows[r], z_rows[r + 1], d_gl, 'B1_GlassLobby')
        if door:
            sm = (s0 + s1) / 2
            box_along(dr, c0, u, n, sm - 0.025, sm + 0.025, z_rows[0], z_rows[1], d_gl, d_gl + 0.1, 'B1_FrameDark')
            for sg in (-1, 1):  # long pull handles either side of the meeting stile
                hs = sm + sg * 0.12
                box_along(dr, c0, u, n, hs - 0.015, hs + 0.015, 0.95, 2.15, d_gl + 0.16, d_gl + 0.19, 'B1_Steel')
                for hz in (1.0, 2.1):
                    box_along(dr, c0, u, n, hs - 0.01, hs + 0.01, hz - 0.01, hz + 0.01, d_gl + 0.1, d_gl + 0.16, 'B1_Steel')
            for sx in (s0 + 0.04, s1 - 0.04):  # heavier door stiles
                box_along(dr, c0, u, n, sx - 0.04, sx + 0.04, z_rows[0], z_rows[1], d_gl, d_gl + 0.1, 'B1_FrameDark')
        # blue - red - blue stripe at eye level (lobby ref photos)
        for zs, mat in ((1.0, 'B1_SignBlue'), (1.07, 'B1_SignRed'), (1.14, 'B1_SignBlue')):
            box_along(dr if door else ef, c0, u, n, s0 + 0.02, s1 - 0.02, zs, zs + 0.04, d_gl - 0.01, d_gl + 0.01, mat)
    for b in range(DOOR_BAYS + 1):
        sx = -half + b * DOOR_BAY_W
        w = 0.07 if 0 < b < DOOR_BAYS else 0.1
        box_along(ef, c0, u, n, sx - w, sx + w, z_rows[0], BASE_H, REC - 0.05, d_gl + 0.12, 'B1_FrameDark')
    for z in z_rows:
        box_along(ef, c0, u, n, -half, half, max(z_rows[0], z - 0.05), min(BASE_H, z + 0.05),
                  REC - 0.05, d_gl + 0.12, 'B1_FrameDark')
    ef.build(coll)

    ob = dr.build(coll)
    if ob:
        ob['noCollide'] = 1      # glTF extras -> userData.noCollide: WalkMode walks through the door leaves

    # ceiling under the ring: only the outdoor strip between the ring line and the recessed front (the door
    # recess included). Behind the glass the lobby model (sanh.py) has its own ceiling, the lecture hall sits above.
    so = MB('Lobby_F1_Soffit')
    s_of = [(p - c0).dot(u) for p in P]
    edge = [c0 + u * s + n * REC if abs(s) < half else p + nn * SHOP_WALL_D[1] for p, nn, s in zip(P, N, s_of)]
    for i in range(NS):
        so.face([V3(edge[i], BASE_H), V3(edge[i + 1], BASE_H), V3(P[i + 1], BASE_H), V3(P[i], BASE_H)],
                'B1_Wall', (0, 0, -1))
    so.build(coll)


# --------------------------------------------------------------------------- ring, floors 3-4 (white)

def ring_rows():
    """Window rows of the ring, bottom to top: 2 glass rows on floor 3, the floor-4 slab band in wall
    material (the sketch's 3rd row), 2 glass rows on floor 4. Sills, heads and the band sit at the same
    heights as the wings' windows and spandrel bands on those floors."""
    f3, f4, f5 = level_top(BASE_LV), level_top(BASE_LV + 1), level_top(BASE_LV + 2)
    lo0, lo1, hi0, hi1 = f3 + 0.95, f4 - 0.35, f4 + 0.95, f5 - 0.35
    lm, hm = lo1 - (lo1 - lo0) * RING_TRANSOM, hi1 - (hi1 - hi0) * RING_TRANSOM
    return [(lo0, lm, RING_GLASS), (lm, lo1, RING_GLASS), (lo1, hi0, 'B1_Wall'),
            (hi0, hm, RING_GLASS), (hm, hi1, RING_GLASS)]


def build_ring(arc, coll):
    P, N, apex, HE = arc['P'], arc['N'], arc['apex'], arc['HE']
    idx = lambda f: int(round(f * NS))
    rows = ring_rows()
    gz0, gz1 = rows[0][0], rows[-1][1]
    # user: nothing of the ring may rise in front of the wings' floor-5 windows, so the cornice sits on the
    # lobby roof (HE) right over the floor-4 windows and the coping stays under the floor-5 sills
    zc = HE - 0.3
    body0 = BASE_H + 0.35
    openings = [(idx(f0), idx(f1), cols) for f0, f1, cols in RING_WINDOWS]

    wl = MB('Lobby_Ring_Wall')
    curved_solid(wl, P, N, 0, NS, BASE_H - 0.05, body0, -0.3, 0.25, 'B1_Wall')       # floor-3 slab ledge
    cur = 0
    for o0, o1, _ in openings:
        curved_solid(wl, P, N, cur, o0, body0, zc, -0.3, 0.0, 'B1_Wall')
        curved_solid(wl, P, N, o0, o1, body0, gz0, -0.3, 0.0, 'B1_Wall')
        curved_solid(wl, P, N, o0, o1, gz1, zc, -0.3, 0.0, 'B1_Wall')
        curved_solid(wl, P, N, o0, o1, gz0 - 0.1, gz0, -0.2, 0.1, 'B1_Wall')            # sill
        for i in (o0, o1):                                                              # reveals
            j = i + 1 if i == o0 else i - 1
            t = (P[j] - P[i]).normalized()
            q = [P[i] + N[i] * -0.2, P[i] + N[i] * -0.2 + t * 0.02, P[i] + t * 0.02, P[i]]
            wl.face([V3(q[0], gz0), V3(q[3], gz0), V3(q[3], gz1), V3(q[0], gz1)], 'B1_Wall', N3(t))
        cur = o1
    curved_solid(wl, P, N, cur, NS, body0, zc, -0.3, 0.0, 'B1_Wall')
    curved_solid(wl, P, N, 0, NS, zc, zc + 0.35, -0.3, 0.3, 'B1_Wall')                   # cornice
    curved_solid(wl, P, N, 0, NS, zc + 0.35, zc + 1.1, -0.3, 0.05, 'B1_Wall')            # parapet
    curved_solid(wl, P, N, 0, NS, zc + 1.1, zc + 1.2, -0.35, 0.12, 'B1_Wall')            # coping
    wl.build(coll)

    # grid of panes, frame lines run through the wall-material slab row as in the sketch
    win = MB('Lobby_Ring_Windows')
    for o0, o1, cols in openings:
        for r, (za, zb, mat) in enumerate(rows):
            ribbon(win, P, N, o0, o1, -0.2, za, zb, mat, smooth=False)
            if r:
                curved_solid(win, P, N, o0, o1, za - 0.035, za + 0.035, -0.2, -0.11, 'B1_Frame')
        for k in range(cols + 1):          # mullions at equal fractional steps, not snapped to arc samples
            Pm, Nm = lerp_arc(P, N, o0 + (o1 - o0) * k / cols, o0 + (o1 - o0) * k / cols + 1e-3, step=1.0)
            t = (Pm[-1] - Pm[0]).normalized()
            p, nn = Pm[0], Nm[0]
            c = [p + nn * -0.2 - t * 0.035, p + nn * -0.2 + t * 0.035,
                 p + nn * -0.11 + t * 0.035, p + nn * -0.11 - t * 0.035]
            prism(win, c, gz0, gz1, 'B1_Frame')
        curved_solid(win, P, N, o0, o1, gz0, gz0 + 0.07, -0.2, -0.11, 'B1_Frame')
        curved_solid(win, P, N, o0, o1, gz1 - 0.07, gz1, -0.2, -0.11, 'B1_Frame')
    win.build(coll)

    rf = MB('Lobby_Roof')
    rf.face([V3(q, HE) for q in P + [apex]], 'B1_Roof', (0, 0, 1))
    rf.build(coll)


# --------------------------------------------------------------------------- porte-cochere

def build_porch(arc, coll):
    P, N = arc['P'], arc['N']
    c0, u, n = tangent_frame(P, N)
    pt = lambda s, d: c0 + u * s + n * d

    cn = MB('Lobby_Canopy')
    # chamfered slab: top outline wider than the bottom outline (sketch sảnh.png, left)
    k = CANOPY_SLOPE
    top = [pt(-CANOPY_HALF, -0.3), pt(CANOPY_HALF, -0.3), pt(CANOPY_HALF, CANOPY_FRONT), pt(-CANOPY_HALF, CANOPY_FRONT)]
    bot = [pt(-CANOPY_HALF + k, -0.3), pt(CANOPY_HALF - k, -0.3), pt(CANOPY_HALF - k, CANOPY_FRONT - k),
           pt(-CANOPY_HALF + k, CANOPY_FRONT - k)]
    cn.face([V3(q, CANOPY_TOP) for q in top], 'B1_Canopy', (0, 0, 1))
    cn.face([V3(q, CANOPY_BOT) for q in bot], 'B1_Canopy', (0, 0, -1))
    for i in range(4):
        a0, a1, b0, b1 = top[i], top[(i + 1) % 4], bot[i], bot[(i + 1) % 4]
        mid = (a0 + a1 + b0 + b1) / 4 - (c0 + n * (CANOPY_FRONT / 2))
        cn.face([V3(b0, CANOPY_BOT), V3(b1, CANOPY_BOT), V3(a1, CANOPY_TOP), V3(a0, CANOPY_TOP)], 'B1_Canopy', N3(mid))
    # lighter dropped ceiling panel next to the building
    box_along(cn, c0, u, n, -3.0 * ENTRY_SCALE, 3.0 * ENTRY_SCALE, CANOPY_BOT - 0.14, CANOPY_BOT, 0.2, 3.0,
              'B1_CanopySoffit')
    cn.build(coll)

    dl = MB('Lobby_Downlights')
    for s in (k * ENTRY_SCALE for k in (-3.8, -2.0, 0.0, 2.0, 3.8)):
        for d in (3.9, 5.1):
            ring = [pt(s, d) + (u * math.cos(a) + n * math.sin(a)) * 0.09
                    for a in (2 * math.pi * j / 10 for j in range(10))]
            dl.face([V3(q, CANOPY_BOT - 0.005) for q in ring], 'B1_Downlight', (0, 0, -1))
    for s in (k * ENTRY_SCALE for k in (-2.0, 0.0, 2.0)):
        ring = [pt(s, 1.6) + (u * math.cos(a) + n * math.sin(a)) * 0.09 for a in (2 * math.pi * j / 10 for j in range(10))]
        dl.face([V3(q, CANOPY_BOT - 0.145) for q in ring], 'B1_Downlight', (0, 0, -1))
    dl.build(coll)

    col = MB('Lobby_Columns')
    for sg in (-1, 1):
        cylinder(col, pt(sg * COL_S, COL_D), COL_R, LANDING_Z, CANOPY_BOT, 'B1_Steel', 32)
        cylinder(col, pt(sg * COL_S, COL_D), COL_R + 0.06, LANDING_Z, LANDING_Z + 0.08, 'B1_Steel', 32)
    col.build(coll)

    st = MB('Lobby_Steps')
    half = DOOR_BAYS * DOOR_BAY_W / 2
    sw = max(CANOPY_HALF + 0.6, half + (N_STEPS - 1) * STEP_TREAD)   # top tier at least as wide as the door frame
    for k in range(N_STEPS):  # tier k is k treads narrower and shorter than the one below it
        inset = k * STEP_TREAD
        box_along(st, c0, u, n, -sw + inset, sw - inset, 0.0, (k + 1) * STEP_H,
                  -0.45, CANOPY_FRONT + 0.3 - inset, 'B1_Stone')
    box_along(st, c0, u, n, -half, half, 0.0, LANDING_Z, REC, -0.45, 'B1_Stone')
    st.build(coll)


def build_lobby(parent):
    arc = arc_frame()
    root = collection(parent, 'B1_Lobby')
    build_f1(arc, collection(root, 'B1_Lobby_F1'))
    build_ring(arc, collection(root, 'B1_Lobby_Ring'))
    build_porch(arc, collection(root, 'B1_Lobby_Porch'))
    return arc
