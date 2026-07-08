import math
from voronoi_lib.point import Point


def extract_cells(dcel, all_sites):
    cells = {}
    for site in all_sites:
        verts = []
        seen = set()
        for he in dcel.half_edges:
            if he.site != site or he.origin is None:
                continue
            pt = he.origin.point
            key = (round(pt.x, 9), round(pt.y, 9))
            if key not in seen:
                seen.add(key)
                verts.append(pt)
            if he.twin and he.twin.origin:
                pt2 = he.twin.origin.point
                key2 = (round(pt2.x, 9), round(pt2.y, 9))
                if key2 not in seen:
                    seen.add(key2)
                    verts.append(pt2)

        if len(verts) < 3:
            continue

        unique = []
        for v in verts:
            if not any(math.hypot(v.x - u.x, v.y - u.y) < 1e-6 for u in unique):
                unique.append(v)

        if len(unique) < 3:
            continue

        unique.sort(key=lambda v: math.atan2(v.y - site.y, v.x - site.x))
        unique.append(unique[0])
        cells[site] = unique

    return cells
