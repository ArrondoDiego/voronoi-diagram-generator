import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x} {self.y})"

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9

    def __hash__(self):
        return hash((round(self.x, 9), round(self.y, 9)))


def circumcenter(a, b, c):
    # Solves the linear system for the circumcenter of three points using
    # Cramer's rule.  Returns None when the points are collinear (denom ≈ 0).
    A1 = 2 * (b.x - a.x)
    B1 = 2 * (b.y - a.y)
    C1 = b.x**2 + b.y**2 - a.x**2 - a.y**2

    A2 = 2 * (c.x - b.x)
    B2 = 2 * (c.y - b.y)
    C2 = c.x**2 + c.y**2 - b.x**2 - b.y**2

    denom = A1 * B2 - A2 * B1
    if abs(denom) < 1e-9:
        return None

    cx = (C1 * B2 - C2 * B1) / denom
    cy = (A1 * C2 - A2 * C1) / denom
    return Point(cx, cy)
