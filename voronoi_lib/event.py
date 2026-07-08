import heapq
from voronoi_lib.point import Point 

class Event:
    SITE = 1
    CIRCLE = 2

    def __init__(self, type_, point):
        self.type = type_
        self.point = point
        self.valid = True

    def __lt__(self, other):
        return (self.point.y > other.point.y) or (
            abs(self.point.y - other.point.y) < 1e-9
            and self.point.x < other.point.x
        )

    def __repr__(self):
        status = "valid" if self.valid else "INVALID"
        return f"{'SITE' if self.type == 1 else 'CIRCLE'}({self.point}, {status})"


class SiteEvent(Event):
    def __init__(self, point):
        super().__init__(Event.SITE, point)


class CircleEvent(Event):
    def __init__(self, point, arc, center, radius):
        super().__init__(Event.CIRCLE, point)
        self.arc = arc
        self.center = center
        self.radius = radius

    def __repr__(self):
        return f"CircleEvent(bottom={self.point}, center={self.center}, valid={self.valid})"


class EventQueue:
    def __init__(self):
        self._heap = []

    def push(self, event):
        heapq.heappush(self._heap, event)

    def pop(self):
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek(self):
        if self._heap:
            return self._heap[0]
        return None

    def is_empty(self):
        return len(self._heap) == 0

    def __len__(self):
        if self._heap:
            return len(self._heap)
        return 0
