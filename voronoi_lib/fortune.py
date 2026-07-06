import math
from voronoi_lib.point import Point, circumcenter
from voronoi_lib.event import Event, SiteEvent, CircleEvent, EventQueue
from voronoi_lib.beachline import Arc, BeachLine
from voronoi_lib.edge import VoronoiEdge


class FortuneVoronoi:
    def __init__(self, points):
        self.points = sorted(points, key=lambda p: (-p.y, p.x))

        self.edges = []
        self.vertices = []

        self._beach = BeachLine()
        self._queue = EventQueue()

        for p in self.points:
            self._queue.push(SiteEvent(p))

    def compute(self):
        while not self._queue.is_empty():
            event = self._queue.pop()

            if not event.valid:
                continue

            if event.type == Event.SITE:
                self._handle_site(event)
            else:
                self._handle_circle(event)

        self._finish_edges()
        return self.edges

    def print_summary(self):
        print(f"Edges: {len(self.edges)}, Vertices: {len(self.vertices)}")
        for i, e in enumerate(self.edges):
            print(f"  Edge {i+1}: {e}")
        for i, v in enumerate(self.vertices):
            print(f"  Vertex {i+1}: {v}")

    def _handle_site(self, event):
        p = event.point

        if self._beach.is_empty():
            self._beach.set_root(Arc(p))
            return

        arc = self._beach.find_arc_above(p, p.y)

        if arc.event is not None:
            arc.event.valid = False
            arc.event = None

        mid_arc = Arc(p)
        left_arc = Arc(arc.site)

        left_arc.prev = arc.prev
        left_arc.next = mid_arc
        left_arc.edge_left = arc.edge_left

        mid_arc.prev = left_arc
        mid_arc.next = arc

        if arc.prev is not None:
            arc.prev.next = left_arc
        elif self._beach.root is arc:
            self._beach.set_root(left_arc)

        arc.prev = mid_arc

        start_y = self._beach.parabola_x(arc.site, p.y, p.x)
        start_point = Point(p.x, start_y)

        edge1 = VoronoiEdge(start_point, left_arc.site, mid_arc.site)
        self.edges.append(edge1)
        mid_arc.edge_left = edge1
        left_arc.edge_right = edge1

        edge2 = VoronoiEdge(start_point, mid_arc.site, arc.site)
        self.edges.append(edge2)
        arc.edge_left = edge2
        mid_arc.edge_right = edge2

        if left_arc.prev is not None:
            self._check_circle_event(left_arc.prev, left_arc, mid_arc, p.y)

        if arc.next is not None:
            self._check_circle_event(mid_arc, arc, arc.next, p.y)

    def _handle_circle(self, event):
        arc = event.arc
        left_arc = arc.prev
        right_arc = arc.next

        if left_arc is None or right_arc is None:
            return

        if left_arc.event is not None:
            left_arc.event.valid = False
            left_arc.event = None
        if right_arc.event is not None:
            right_arc.event.valid = False
            right_arc.event = None

        vertex = event.center
        self.vertices.append(vertex)

        if arc.edge_left is not None:
            arc.edge_left.end = vertex
        if arc.edge_right is not None:
            arc.edge_right.end = vertex

        left_arc.next = right_arc
        right_arc.prev = left_arc

        new_edge = VoronoiEdge(vertex, left_arc.site, right_arc.site)
        self.edges.append(new_edge)
        left_arc.edge_right = new_edge
        right_arc.edge_left = new_edge

        if left_arc.prev is not None:
            self._check_circle_event(left_arc.prev, left_arc, right_arc, event.point.y)
        if right_arc.next is not None:
            self._check_circle_event(left_arc, right_arc, right_arc.next, event.point.y)

    def _check_circle_event(self, left, mid, right, sweep_y):
        if left is None or mid is None or right is None:
            return
        if left.site == right.site:
            return

        center = circumcenter(left.site, mid.site, right.site)
        if center is None:
            return

        dx = center.x - left.site.x
        dy = center.y - left.site.y
        radius = math.sqrt(dx * dx + dy * dy)
        bottom_y = center.y - radius

        if bottom_y >= sweep_y:
            return

        v1_x = mid.site.x - left.site.x
        v1_y = mid.site.y - left.site.y
        v2_x = right.site.x - mid.site.x
        v2_y = right.site.y - mid.site.y

        cross_product = v1_x * v2_y - v1_y * v2_x

        if cross_product >= -1e-9:
            return

        event_point = Point(center.x, bottom_y)
        event = CircleEvent(event_point, mid, center, radius)
        mid.event = event
        self._queue.push(event)

    def _finish_edges(self):
        for edge in self.edges:
            dx = edge.right.x - edge.left.x
            dy = edge.right.y - edge.left.y
            length = math.sqrt(dx * dx + dy * dy)
            if length == 0:
                continue

            nx = -dy / length
            ny = dx / length

            if edge.start is None and edge.end is None:
                mx = (edge.left.x + edge.right.x) / 2
                my = (edge.left.y + edge.right.y) / 2
                edge.start = Point(mx + nx * 1000, my + ny * 1000)
                edge.end = Point(mx - nx * 1000, my - ny * 1000)
            elif edge.end is None:
                edge.end = Point(
                    edge.start.x - nx * 1000,
                    edge.start.y - ny * 1000,
                )
            elif edge.start is None:
                edge.start = Point(
                    edge.end.x + nx * 1000,
                    edge.end.y + ny * 1000,
                )
