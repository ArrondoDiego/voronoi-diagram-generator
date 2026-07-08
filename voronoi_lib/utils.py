import math
from voronoi_lib.point import Point

def extract_cells(dcel, all_sites):
    # Collects the vertex sequence for each site's Voronoi cell from the DCEL.
    # - Gathers all endpoints of half-edges belonging to the site.
    # - Adds bounding-box corners whose nearest site is this one (so cells
    #   that extend to the box perimeter form closed polygons).
    # - Sorts vertices angularly around the site to produce a correct winding order.
    cells = {}
    
    if all_sites:
        xs = [pt.x for pt in all_sites] + [v.point.x for v in dcel.vertices]
        ys = [pt.y for pt in all_sites] + [v.point.y for v in dcel.vertices]
        margin = 1000
        min_x = min(xs) - margin
        max_x = max(xs) + margin
        min_y = min(ys) - margin
        max_y = max(ys) + margin
        
        box_corners = [
            Point(min_x, min_y), Point(max_x, min_y),
            Point(max_x, max_y), Point(min_x, max_y)
        ]
    else:
        box_corners = []

    for site in all_sites:
        verts = []
        seen = set()
        
        for he in dcel.half_edges:
            if he.site != site or he.origin is None:
                continue
            
            pt1 = he.origin.point
            key1 = (round(pt1.x, 9), round(pt1.y, 9))
            if key1 not in seen:
                seen.add(key1)
                verts.append(pt1)
                
            if he.twin and he.twin.origin:
                pt2 = he.twin.origin.point
                key2 = (round(pt2.x, 9), round(pt2.y, 9))
                if key2 not in seen:
                    seen.add(key2)
                    verts.append(pt2)
                    
        for corner in box_corners:
            closest_site = min(all_sites, key=lambda s: (s.x - corner.x)**2 + (s.y - corner.y)**2)
            if closest_site == site:
                key_c = (round(corner.x, 9), round(corner.y, 9))
                if key_c not in seen:
                    seen.add(key_c)
                    verts.append(corner)

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