"""Event queue for Fortune's sweepline algorithm.

Defines site events (triggered when the sweep line hits a new site)
and circle events (triggered when three arcs converge to a point).
"""

import heapq
from voronoi_lib.point import Point


class Event:
    """Base class for events in the priority queue.

    Attributes:
        type: Event.SITE or Event.CIRCLE to distinguish the two kinds.
        point: The Point at which this event occurs.
        valid: True if this event is still relevant; False for deleted
               false-alarm events that should be skipped when popped.
    """

    SITE = 1
    CIRCLE = 2

    def __init__(self, type_, point):
        self.type = type_
        self.point = point
        self.valid = True

    def __lt__(self, other):
        """Order by decreasing y (sweep line descends), tie-break by x."""
        return (self.point.y > other.point.y) or (
            abs(self.point.y - other.point.y) < 1e-9
            and self.point.x < other.point.x
        )

    def __repr__(self):
        status = "valid" if self.valid else "INVALID"
        return f"{'SITE' if self.type == 1 else 'CIRCLE'}({self.point}, {status})"


class SiteEvent(Event):
    """Event fired when the sweep line reaches a new site point."""

    def __init__(self, point):
        super().__init__(Event.SITE, point)


class CircleEvent(Event):
    """Event fired when three consecutive beach-line arcs converge.

    Attributes:
        arc: The BeachNode of the middle arc (the one that disappears).
        center: The circumcenter of the three sites (the Voronoi vertex).
        radius: The radius of the circle defined by the three sites.
    """

    def __init__(self, point, arc, center, radius):
        super().__init__(Event.CIRCLE, point)
        self.arc = arc
        self.center = center
        self.radius = radius

    def __repr__(self):
        return f"CircleEvent(bottom={self.point}, center={self.center}, valid={self.valid})"


class EventQueue:
    """Priority queue for sweep-line events backed by a binary heap.

    The minimum element (by Event.__lt__ ordering) is the event with
    the highest y-coordinate — the next to be processed by the sweep.
    """

    def __init__(self):
        self._heap = []

    def push(self, event):
        """Insert a new event into the queue."""
        heapq.heappush(self._heap, event)

    def pop(self):
        """Remove and return the event with the highest y-coordinate."""
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek(self):
        """Return the next event without removing it, or None if empty."""
        if self._heap:
            return self._heap[0]
        return None

    def is_empty(self):
        """Check whether the queue contains any events."""
        return len(self._heap) == 0

    def __len__(self):
        return len(self._heap)
