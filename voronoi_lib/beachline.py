import math
from voronoi_lib.point import Point

class Arc:
    def __init__(self, site):
        self.site = site
        self.prev = None
        self.next = None
        self.event = None
        self.edge_left = None
        self.edge_right = None

    def __repr__(self):
        return f"Arc({self.site})"


class BeachLine:
    def __init__(self):
        self._root = None

    @property
    def root(self):
        return self._root

    def set_root(self, arc):
        self._root = arc

    def is_empty(self):
        return self._root is None

    def insert_after(self, anchor, new_arc):
        new_arc.prev = anchor
        new_arc.next = anchor.next
        if anchor.next:
            anchor.next.prev = new_arc
        anchor.next = new_arc

    def remove(self, arc):
        if arc.prev:
            arc.prev.next = arc.next
        if arc.next:
            arc.next.prev = arc.prev
        if arc is self._root:
            self._root = arc.next

    def parabola_x(self, site, directrix_y, x_query):
        if abs(site.y - directrix_y) < 1e-9:
            return -float('inf')
        return (x_query - site.x)**2 / (2 * (site.y - directrix_y)) + (site.y + directrix_y) / 2

    def find_arc_above(self, point, sweep_y):
        if self._root is None:
            return None

        arc = self._root
        while arc.next is not None:
            bps = self.get_breakpoints(arc, arc.next, sweep_y)
            if bps is None:
                return arc

            if arc.site.y < arc.next.site.y:
                active_bp = bps[1]
            else:
                active_bp = bps[0]

            if point.x < active_bp:
                return arc
            arc = arc.next
        return arc

    def get_breakpoints(self, left, right, sweep_y):
        p1, p2 = left.site, right.site
        d = sweep_y

        if abs(p1.y - d) < 1e-9 and abs(p2.y - d) < 1e-9:
            return None
        if abs(p1.y - d) < 1e-9:
            x = p1.x
            return (x, x)
        if abs(p2.y - d) < 1e-9:
            x = p2.x
            return (x, x)

        a = 1 / (p1.y - d) - 1 / (p2.y - d)

        if abs(a) < 1e-9:
            x = (p1.x + p2.x) / 2
            return (x, x)

        b = -2 * p1.x / (p1.y - d) + 2 * p2.x / (p2.y - d)
        c = (p1.x**2 + p1.y**2 - d**2) / (p1.y - d) - (p2.x**2 + p2.y**2 - d**2) / (p2.y - d)

        disc = b * b - 4 * a * c
        if disc < 0:
            return None

        x1 = (-b - math.sqrt(disc)) / (2 * a)
        x2 = (-b + math.sqrt(disc)) / (2 * a)
        return (x1, x2) if x1 < x2 else (x2, x1)
