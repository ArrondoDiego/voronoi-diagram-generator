import math
import random
from collections import defaultdict
from voronoi_lib.point import Point
from voronoi_lib.fortune import FortuneVoronoi
from voronoi_lib.clipping import clip_polygon
from voronoi_lib.visualization import save_image

DEBUG = True

def extract_cells(edges):
    cell_vertices = defaultdict(set)

    for edge in edges:
        if edge.start is not None:
            cell_vertices[edge.left].add(edge.start)
            cell_vertices[edge.right].add(edge.start)
        if edge.end is not None:
            cell_vertices[edge.left].add(edge.end)
            cell_vertices[edge.right].add(edge.end)

    cells = {}
    for site, vertices in cell_vertices.items():
        sorted_vertices = sorted(
            list(vertices),
            key=lambda v: math.atan2(v.y - site.y, v.x - site.x)
        )
        cells[site] = sorted_vertices

    return cells

def main():
    choice = input("Use [r]andom or [c]ustom points?: ").strip().lower()
    points = []

    if choice == "c":
        print("Enter 5 points (x y) between -100 and 100:")
        for i in range(5):
            while True:
                try:
                    x, y = map(int, input(f"  {i+1}: ").split())
                    if 0 <= x <= 100 and 0 <= y <= 100:
                        points.append(Point(x, y))
                        break 
                    else:
                        print(" Coordinates must be between -100 and 100")
                except ValueError:
                    print(" Invalid, use: x y")
    else:  # choice r
        for _ in range(5):
            points.append(Point(random.randint(0, 100), random.randint(0, 100)))
        for i, p in enumerate(points, 1):
            print(f"  Point {i}: ({p.x}, {p.y})")

    v = FortuneVoronoi(points)
    edges = v.compute()
    print(f"\n{len(edges)} edges, {len(v.vertices)} vertices")
    cells = extract_cells(edges)
    if DEBUG: 
        print("\n--- VORONOI CELLS ---\n")
        for i, (site, vertices) in enumerate(cells.items(), 1):
            print(f"Cell for Site {site}:")
            for vert in vertices:
                print(f"- Vertex ({vert.x:.2f}, {vert.y:.2f})")
    
    # sizes of canvas to save the image
    box = [
        Point(0, 0),
        Point(100, 0),
        Point(100, 100),
        Point(0, 100)
    ]
    
    clipped_cells = {}
    for site, vertices in cells.items():
        clipped_vertices = clip_polygon(vertices, box)
        if clipped_vertices:
            clipped_cells[site] = clipped_vertices

    save_image(points, clipped_cells, box, "voronoi_output.png")

if __name__ == "__main__":
    main()