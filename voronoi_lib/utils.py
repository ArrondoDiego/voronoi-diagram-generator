from collections import defaultdict
from voronoi_lib.point import Point
import math 

def ray_box_intersection(start, direction, box):
    min_x = min(p.x for p in box)
    max_x = max(p.x for p in box)
    min_y = min(p.y for p in box)
    max_y = max(p.y for p in box)
    
    t_min = float('inf')
    pt = None

    # Controlla lati verticali (x = min_x, x = max_x)
    if abs(direction.x) > 1e-9:
        t1 = (min_x - start.x) / direction.x
        if t1 > 1e-9 and t1 < t_min:
            t_min = t1
            pt = Point(min_x, start.y + t1 * direction.y)
            
        t2 = (max_x - start.x) / direction.x
        if t2 > 1e-9 and t2 < t_min:
            t_min = t2
            pt = Point(max_x, start.y + t2 * direction.y)

    # Controlla lati orizzontali (y = min_y, y = max_y)
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

def extract_cells(edges, universe_box):
    cell_vertices = defaultdict(set)

    for edge in edges:
        if getattr(edge, 'start', None):
            cell_vertices[edge.left].add(edge.start)
            cell_vertices[edge.right].add(edge.start)
            
        if getattr(edge, 'end', None):
            cell_vertices[edge.left].add(edge.end)
            cell_vertices[edge.right].add(edge.end)
            
        elif getattr(edge, 'direction', None):
            # È un raggio infinito: calcoliamo dove esce dal Bounding Box dell'Universo
            pt = ray_box_intersection(edge.start, edge.direction, universe_box)
            if pt:
                cell_vertices[edge.left].add(pt)
                cell_vertices[edge.right].add(pt)

    cells = {}
    for site, vertices in cell_vertices.items():
        # Ordinamento radiale per formare un poligono convesso valido
        sorted_vertices = sorted(
            list(vertices),
            key=lambda v: math.atan2(v.y - site.y, v.x - site.x)
        )
        cells[site] = sorted_vertices

    return cells