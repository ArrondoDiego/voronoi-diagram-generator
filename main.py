import math
import random
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
    else:
        for _ in range(5):
            points.append(Point(random.randint(0, 100), random.randint(0, 100)))
        for i, p in enumerate(points, 1):
            print(f"  Point {i}: ({p.x}, {p.y})")

    display_box = [Point(0, 0), Point(100, 0), Point(100, 100), Point(0, 100)]

    v = FortuneVoronoi(points)
    dcel = v.compute()

    cells = extract_cells(dcel, points)
    clipped_cells = {}
    for site, vertices in cells.items():
        clipped_vertices = clip_polygon(vertices, display_box)
        if clipped_vertices:
            clipped_cells[site] = clipped_vertices

    save_image(points, clipped_cells, display_box, "voronoi_output.png")

    if DEBUG:
        print(f"\nDCEL: {len(dcel.vertices)} vertices, "
              f"{len(dcel.half_edges)} half-edges, "
              f"{len(dcel.faces)} faces")


if __name__ == "__main__":
    main()
