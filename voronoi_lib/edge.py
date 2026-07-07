from voronoi_lib.point import Point

class VoronoiEdge:
    def __init__(self, start, left, right):
        self.start = start
        self.end = None
        self.left = left
        self.right = right
        self.direction = None  # Nuovo: Vettore direzionale (dx, dy) per le semirette
        self.finished = False

    def __repr__(self):
        if self.end:
            return f"Edge({self.start} -> {self.end}, L:{self.left} R:{self.right})"
        return f"Ray({self.start} -> dir:{self.direction}, L:{self.left} R:{self.right})"