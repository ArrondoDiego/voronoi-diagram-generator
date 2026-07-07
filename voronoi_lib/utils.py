import math
from collections import defaultdict
from voronoi_lib.point import Point

def ray_box_intersection(start, direction, box):
    min_x = min(p.x for p in box)
    max_x = max(p.x for p in box)
    min_y = min(p.y for p in box)
    max_y = max(p.y for p in box)
    
    t_min = float('inf')
    pt = None

    if abs(direction.x) > 1e-9:
        t1 = (min_x - start.x) / direction.x
        if t1 > 1e-9 and t1 < t_min:
            t_min = t1
            pt = Point(min_x, start.y + t1 * direction.y)
            
        t2 = (max_x - start.x) / direction.x
        if t2 > 1e-9 and t2 < t_min:
            t_min = t2
            pt = Point(max_x, start.y + t2 * direction.y)

    if abs(direction.y) > 1e-9:
        t3 = (min_y - start.y) / direction.y
        if t3 > 1e-9 and t3 < t_min:
            t_min = t3
            pt = Point(start.x + t3 * direction.x, min_y)

        t4 = (max_y - start.y) / direction.y
        if t4 > 1e-9 and t4 < t_min:
            t_min = t4
            pt = Point(start.x + t4 * direction.x, max_y)

    return pt

def dist_sq(p, s):
    return (p.x - s.x)**2 + (p.y - s.y)**2

def extract_cells(edges, universe_box, all_sites):
    cell_vertices = defaultdict(list)

    for edge in edges:
        if getattr(edge, 'start', None):
            cell_vertices[edge.left].append(edge.start)
            cell_vertices[edge.right].append(edge.start)
            
        if getattr(edge, 'end', None):
            cell_vertices[edge.left].append(edge.end)
            cell_vertices[edge.right].append(edge.end)
            
        elif getattr(edge, 'direction', None):
            dir_x, dir_y = edge.direction.x, edge.direction.y
            start_pt = edge.start
            
            test_t = 1000
            pt1 = Point(start_pt.x + dir_x * test_t, start_pt.y + dir_y * test_t)
            pt2 = Point(start_pt.x - dir_x * test_t, start_pt.y - dir_y * test_t)
            
            dist1 = dist_sq(pt1, edge.left)
            v1 = sum(1 for s in all_sites if s != edge.left and s != edge.right and dist_sq(pt1, s) < dist1)
            dist2 = dist_sq(pt2, edge.left)
            v2 = sum(1 for s in all_sites if s != edge.left and s != edge.right and dist_sq(pt2, s) < dist2)
            
            final_dir = edge.direction if v1 <= v2 else Point(-dir_x, -dir_y)
            
            pt = ray_box_intersection(start_pt, final_dir, universe_box)
            if pt:
                cell_vertices[edge.left].append(pt)
                cell_vertices[edge.right].append(pt)

    cells = {}
    for site, vertices in cell_vertices.items():
        # 1. PULIZIA: Rimuoviamo i duplicati generati dai float
        unique_verts = []
        for v in vertices:
            if not any(math.hypot(v.x - u.x, v.y - u.y) < 1e-6 for u in unique_verts):
                unique_verts.append(v)
        
        if len(unique_verts) < 3:
            continue

        # 2. ORDINAMENTO: Ora math.atan2 funzionerà perfettamente
        sorted_vertices = sorted(
            unique_verts,
            key=lambda v: math.atan2(v.y - site.y, v.x - site.x)
        )
        
        # 3. CHIUSURA: Per assicurarci che Sutherland-Hodgman non salti l'ultimo spigolo
        if sorted_vertices:
            sorted_vertices.append(sorted_vertices[0])
            
        cells[site] = sorted_vertices

    return cells