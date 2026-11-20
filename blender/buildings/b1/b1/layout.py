"""Parametric, mirror-symmetric footprint of B1 (replaces building the massing from OSM edges).

The OSM export was only used to plan it: the V's inner corner, its bisector, the 90 deg opening, the storey
counts, the arm depth and the bulge of the lobby arc come from there. Every facade with windows is a whole
number of BAY_W bays so the (square) cluster windows fit without being stretched. User: the front of each arm
has 3 / 1 / 1 window bays on the 10 / 8 / 5 storey blocks (the 10-storey bays all visible beside the stair tower,
photo 7; the lower blocks are single-bay steps); the corner zone behind the tower is plain wall, and the lobby
covers it plus the next 2 bays. The back of the 10-storey block is window bays up to a narrow solid corner pier.

Plan coordinates on an arm: s = distance along the arm from the inner corner, t = distance from the front
(courtyard) face towards the back. Both arms come from the same function, so they mirror exactly.
"""
import math

from mathutils import Vector

from .config import BAY_W, ENTRANCE_PART, level_top
from .geom import area2

CORNER = Vector((-2.9, -14.1))               # inner corner of the V (OSM node 8158144805)
AXIS = Vector((0.057, 0.998)).normalized()   # V bisector, pointing into the courtyard (OSM: ~3 deg east of north)
ARM_W = 12.44                                # arm depth front to back (OSM)
TOWER_R, TOWER_D = 4.2, 2.0                  # stair tower radius, and its centre's distance from CORNER along AXIS
TOWER_ZONE = 6.0                             # plain wall in the corner, just hidden behind the tower and its bands
BLOCKS = [(10, 3), (8, 1), (5, 1)]           # (storeys, front window bays), from the tower zone outwards
LOBBY_BAYS = 2                               # window bays covered by the lobby, after the tower zone (photo 7)
LOBBY_LEVELS = 4
LOBBY_BULGE = 0.30                           # arc sagitta / half chord (OSM)
ARM_LEN = TOWER_ZONE + BAY_W * sum(b for _, b in BLOCKS)
LOBBY_ARC_SAMPLES = 24                       # resolution of the lobby outline in the parts dict


def rot(v, deg):
    a = math.radians(deg)
    return Vector((v.x * math.cos(a) - v.y * math.sin(a), v.x * math.sin(a) + v.y * math.cos(a)))


ARMS = {'E': rot(AXIS, -45.0), 'W': rot(AXIS, 45.0)}   # direction of each arm from the corner
STATIONS = [TOWER_ZONE]                                  # s of the tower zone's end and of each block's outer end
for _, bays in BLOCKS:
    STATIONS.append(STATIONS[-1] + bays * BAY_W)
# back of the 10-storey block: as many whole window bays as fit from its gable to the outer corner O
# (user: windows there, not a blank core); the remainder (~1.6 m) is a solid pier at the corner
BACK_BAYS = int((STATIONS[1] + ARM_W) // BAY_W)


def arm_pt(side, s, t):
    d = ARMS[side]
    back = -ARMS['W' if side == 'E' else 'E']
    return CORNER + d * s + back * t


NODES = {'C': CORNER.copy(), 'O': CORNER - (ARMS['E'] + ARMS['W']) * ARM_W}   # O = outer corner of the V
for _side in 'EW':
    NODES[f'{_side}_tower'] = arm_pt(_side, STATIONS[0], 0.0)
    NODES[f'{_side}_bk'] = arm_pt(_side, STATIONS[1] - BACK_BAYS * BAY_W, ARM_W)   # back bays end; solid pier to O
    NODES[f'{_side}_lobby'] = arm_pt(_side, STATIONS[0] + LOBBY_BAYS * BAY_W, 0.0)
    for _k, _s in enumerate(STATIONS[1:], 1):
        NODES[f'{_side}_f{_k}'] = arm_pt(_side, _s, 0.0)
        NODES[f'{_side}_b{_k}'] = arm_pt(_side, _s, ARM_W)

# faces across an arm (block steps and the outer ends) get the gable treatment
END_EDGES = {frozenset((f'{side}_f{k}', f'{side}_b{k}')) for side in 'EW' for k in range(1, len(BLOCKS) + 1)}
SIGN_EDGE = frozenset(('W_f1', 'W_b1'))      # west gable of the 10-storey block, seen in ref.jpg
PLAIN_EDGES = {frozenset(('C', 'E_tower')), frozenset(('C', 'W_tower'))}   # tower bays: plain wall, no parapet
GABLE_WIN_T = 0.22   # user: the column of small gable windows sits near the front edge, as under the B1 sign


def gable_win_t(ra, rb):
    """Position of a gable's window column as a fraction from node ra: near the front (courtyard) corner."""
    if '_f' in ra:
        return GABLE_WIN_T
    if '_f' in rb:
        return 1.0 - GABLE_WIN_T
    return 0.5
# (gable edge of the 10-storey block, distance inward, size along edge, size inward, height); mirrored pair,
# the first one carries the mast and the water tanks (west, as in the photos)
PENTHOUSE_EDGES = [(SIGN_EDGE, 9.0, 8.0, 7.0, 4.2), (frozenset(('E_f1', 'E_b1')), 9.0, 8.0, 7.0, 4.2)]


def lobby_arc(n):
    """n + 1 points on the lobby arc from its west end to its east end, and the circle (centre, radius)."""
    a, c = NODES['W_lobby'], NODES['E_lobby']
    half = (c - a).length / 2
    sag = LOBBY_BULGE * half
    R = (half * half + sag * sag) / (2 * sag)
    cen = (a + c) / 2 + AXIS * (sag - R)
    th0 = math.atan2(a.y - cen.y, a.x - cen.x)
    th1 = math.atan2(c.y - cen.y, c.x - cen.x)
    span = (th1 - th0 + math.pi) % math.tau - math.pi     # the arc is under 180 deg: take the short way
    pts = [cen + Vector((math.cos(th0 + span * i / n), math.sin(th0 + span * i / n))) * R for i in range(n + 1)]
    return pts, cen, R


def part(pid, refs, levels, pts=None):
    pts = pts or [NODES[r].copy() for r in refs]
    if area2(pts) < 0:
        refs, pts = refs[::-1], pts[::-1]
    return pid, {'id': pid, 'refs': refs, 'pts': pts, 'levels': levels, 'h': level_top(levels)}


def build_parts():
    """Same structure as the old OSM building:part dict; parts sharing an edge share its node names."""
    n = len(BLOCKS)
    info = dict([part('B1_10F', ['C', 'E_tower', 'E_lobby', 'E_f1', 'E_b1', 'E_bk', 'O',
                                 'W_bk', 'W_b1', 'W_f1', 'W_lobby', 'W_tower'], BLOCKS[0][0])])
    for side in 'EW':
        for k in range(1, n):
            info.update([part(f'B1_{BLOCKS[k][0]:02d}F_{side}',
                              [f'{side}_f{k}', f'{side}_f{k + 1}', f'{side}_b{k + 1}', f'{side}_b{k}'], BLOCKS[k][0])])
    arc, _, _ = lobby_arc(LOBBY_ARC_SAMPLES)
    refs = ['C', 'W_tower', 'W_lobby'] + [f'arc{i}' for i in range(1, LOBBY_ARC_SAMPLES)] + ['E_lobby', 'E_tower']
    pts = [CORNER.copy(), NODES['W_tower'].copy()] + arc + [NODES['E_tower'].copy()]
    info.update([part(ENTRANCE_PART, refs, LOBBY_LEVELS, pts)])
    return info
