from voronoi_lib.point import Point

class VoronoiEdge:
    def __init__(self, start, left, right):
        self.start = start
        self.end = None
        self.left = left
        self.right = right
        self.finished = False

    def __repr__(self):
        return (
            f"Edge({self.start} -> {self.end}, "
            f"L:{self.left} R:{self.right})"
        )
