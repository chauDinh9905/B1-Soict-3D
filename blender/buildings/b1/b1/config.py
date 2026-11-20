"""Shared dimensions, OSM ids and build switches for the B1 model."""

B1_WAY = '184021007'
ENTRANCE_PART = '1207082389'

GROUND_H = 4.5      # ground floor storey height (m)
FLOOR_H = 3.6       # typical storey height (m)
PARAPET = 1.0
BAND_D = 0.35       # projection of the horizontal spandrel bands
PIL_D = 0.45        # projection of the vertical pilasters
PIL_W = 0.5
# structural bay = one cluster window. User: the 3 windows of a cluster must look square, so each is as wide as a
# typical storey's window is tall (FLOOR_H - 0.95 sill - 0.35 head = 2.3 m), plus 2 x 0.5 m panels and a pilaster
BAY_W = 3 * (FLOOR_H - 1.3) + 2 * 0.5 + PIL_W   # = 8.4 m

BUILD_CONTEXT = False  # roads, neighbours, cars, trees: off while we focus on the building itself
# (context is still placed from OSM and no longer matches the parametric footprint in layout.py)


def level_top(lv):
    return 0.0 if lv <= 0 else GROUND_H + (lv - 1) * FLOOR_H
