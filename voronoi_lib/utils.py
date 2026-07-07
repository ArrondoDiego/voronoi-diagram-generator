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

def extract_cells(edges, universe_box, all_sites):
    cell_vertices = defaultdict(set)

    # Helper analitico per la distanza al quadrato
    def dist_sq(p, s):
        return (p.x - s.x)**2 + (p.y - s.y)**2

    for edge in edges:
        if getattr(edge, 'start', None):
            cell_vertices[edge.left].add(edge.start)
            cell_vertices[edge.right].add(edge.start)
            
        if getattr(edge, 'end', None):
            cell_vertices[edge.left].add(edge.end)
            cell_vertices[edge.right].add(edge.end)
            
        elif getattr(edge, 'direction', None):
            # IL TEST INFALLIBILE
            # Testiamo empiricamente quale dei due versi del raggio si allontana dal diagramma
            test_t = 10000
            dir_x, dir_y = edge.direction.x, edge.direction.y
            start_pt = edge.start
            
            # Generiamo due punti lontanissimi nelle due direzioni opposte
            pt1 = Point(start_pt.x + dir_x * test_t, start_pt.y + dir_y * test_t)
            pt2 = Point(start_pt.x - dir_x * test_t, start_pt.y - dir_y * test_t)
            
            # Calcoliamo quante volte pt1 è più vicino a un altro sito rispetto al suo sito legittimo (edge.left)
            dist1 = dist_sq(pt1, edge.left)
            violations1 = sum(1 for s in all_sites if s != edge.left and s != edge.right and dist_sq(pt1, s) < dist1)
            
            # Facciamo lo stesso per pt2
            dist2 = dist_sq(pt2, edge.left)
            violations2 = sum(1 for s in all_sites if s != edge.left and s != edge.right and dist_sq(pt2, s) < dist2)
            
            # La verità geometrica: la direzione corretta esce verso il vuoto, subendo meno violazioni
            final_dir = edge.direction if violations1 <= violations2 else Point(-dir_x, -dir_y)
            
            # Calcoliamo l'intersezione solo con la direzione confermata
            pt = ray_box_intersection(start_pt, final_dir, universe_box)
            if pt:
                cell_vertices[edge.left].add(pt)
                cell_vertices[edge.right].add(pt)

    cells = {}
    for site, vertices in cell_vertices.items():
        # L'ordinamento ripristinerà il poligono convesso perfetto
        sorted_vertices = sorted(
            list(vertices),
            key=lambda v: math.atan2(v.y - site.y, v.x - site.x)
        )
        cells[site] = sorted_vertices

    return cells

# All'interno di extract_cells in utils.py
