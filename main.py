import math
import random
from collections import defaultdict
from voronoi_lib.point import Point
from voronoi_lib.fortune import FortuneVoronoi
from voronoi_lib.clipping import clip_polygon
from voronoi_lib.visualization import save_image
from voronoi_lib.utils import extract_cells

DEBUG = True

def main():
    choice = input("Use [r]andom or [c]ustom points?: ").strip().lower()
    points = []

    if choice == "c":
        print("Enter 5 points (x y) between 0 and 100:")
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

    # 1. Definizione dei due domini
    universe_box = [Point(-10000, -10000), Point(10000, -10000), Point(10000, 10000), Point(-10000, 10000)]
    display_box = [Point(0, 0), Point(100, 0), Point(100, 100), Point(0, 100)]
    
    # 2. Computazione
    v = FortuneVoronoi(points)
    edges = v.compute()
    
    # 3. Estrazione chiusa all'infinito
    cells = extract_cells(edges, universe_box, points)    
    # 4. Clipping geometrico esatto per lo schermo
    clipped_cells = {}
    for site, vertices in cells.items():
        clipped_vertices = clip_polygon(vertices, display_box)
        if clipped_vertices:
            clipped_cells[site] = clipped_vertices

    save_image(points, clipped_cells, display_box, "voronoi_output.png")

if __name__ == "__main__":
    main()