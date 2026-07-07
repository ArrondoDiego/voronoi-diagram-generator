from voronoi_lib.point import Point

class VoronoiEdge:
    def __init__(self, start, left_site, right_site):
        self.start = start
        self.end = None
        self.left = left_site
        self.right = right_site
        self.direction = None # Vettore (dx, dy) che punta all'infinito

    def __repr__(self):
        end_str = self.end if self.end else f"Ray(dir={self.direction})"
        return (
            f"Edge({self.start} -> {end_str}, "
            f"L:{self.left} R:{self.right})"
        )