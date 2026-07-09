"""Fortune's algorithm for computing Voronoi diagrams.

This module implements the core sweepline algorithm as described in
de Berg et al., "Computational Geometry: Algorithms and Applications"
(Chapter 7).  The FortuneVoronoi class processes site and circle
events, maintains the beach line status structure, and constructs
the Voronoi diagram as a DCEL.
"""

import math
from voronoi_lib.point import Point, circumcenter
from voronoi_lib.event import Event, SiteEvent, CircleEvent, EventQueue
from voronoi_lib.edge import DCEL
from voronoi_lib.beachline import BeachNode, BeachLine


class FortuneVoronoi:
    """Main solver for the Voronoi diagram of a set of point sites.

    Usage:
        v = FortuneVoronoi(points)
        dcel = v.compute()

    The compute() method runs the full algorithm and returns a DCEL
    containing all vertices, half-edges, and faces of the diagram.
    """

    def __init__(self, points):
        """Initialise the event queue, beach line, and DCEL.

        Sorts points by decreasing y (top-to-bottom sweep order) and
        pushes a SiteEvent for each one.
        """
        self.points = sorted(points, key=lambda p: (-p.y, p.x))

        self.dcel = DCEL()

        self._beach = BeachLine()
        self._queue = EventQueue()

        for p in self.points:
            self._queue.push(SiteEvent(p))

    def compute(self):
        """Run the main sweepline loop and post-processing.

        Returns the completed DCEL with all faces built.
        """
        while not self._queue.is_empty():
            event = self._queue.pop()

            if not event.valid:
                continue

            if event.type == Event.SITE:
                self._handle_site(event)
            else:
                self._handle_circle(event)

        self._attach_to_bounding_box()
        self._build_faces()
        return self.dcel

    # ------------------------------------------------------------------
    # Site event handling
    # ------------------------------------------------------------------

    def _handle_site(self, event):
        """Process a site event (steps 1-5 of HANDLESITEEVENT).

        When the sweep line reaches a new site, the arc above it is
        split into three arcs (left, middle=new site, right) separated
        by two new breakpoints.  Half-edges for the new Voronoi edge
        are created, and potential circle events are checked.
        """
        p = event.point

        # Step 1: empty beach line — just insert the first arc.
        if self._beach.is_empty():
            self._beach.set_root(BeachNode(p, is_leaf=True))
            return

        # Step 2: find the arc vertically above the new site.
        arc = self._beach.find_arc_above(p, p.y)

        # If this arc had a pending circle event, it is now a false alarm.
        if arc.event is not None:
            arc.event.valid = False
            arc.event = None

        # Geometric start point of the new edge (the intersection of
        # the new parabola with the existing one at the sweep position).
        start_y = self._beach.parabola_x(arc.site, p.y, p.x)
        start_point = Point(p.x, start_y)

        # Step 3: replace the arc with three new arcs and two breakpoints.
        left_leaf = BeachNode(arc.site, is_leaf=True)
        mid_leaf = BeachNode(p, is_leaf=True)
        right_leaf = BeachNode(arc.site, is_leaf=True)

        # Update the doubly-linked arc list.
        left_leaf.prev = arc.prev
        if arc.prev:
            arc.prev.next = left_leaf
        left_leaf.next = mid_leaf

        mid_leaf.prev = left_leaf
        mid_leaf.next = right_leaf

        right_leaf.prev = mid_leaf
        right_leaf.next = arc.next
        if arc.next:
            arc.next.prev = right_leaf

        # Create breakpoint nodes.
        bp_left = BeachNode(is_leaf=False)
        bp_left.left_site = arc.site
        bp_left.right_site = p

        bp_right = BeachNode(is_leaf=False)
        bp_right.left_site = p
        bp_right.right_site = arc.site

        # Build the subtree structure.
        bp_left.left = left_leaf
        left_leaf.parent = bp_left

        bp_left.right = bp_right
        bp_right.parent = bp_left

        bp_right.left = mid_leaf
        mid_leaf.parent = bp_right

        bp_right.right = right_leaf
        right_leaf.parent = bp_right

        # Attach the subtree to the old arc's parent.
        bp_left.parent = arc.parent
        if arc.parent is None:
            self._beach.set_root(bp_left)
        else:
            if arc.parent.left == arc:
                arc.parent.left = bp_left
            else:
                arc.parent.right = bp_left

        self._beach.rebalance(bp_left)

        # Step 4: create half-edge records for the new Voronoi edge.
        he_left, he_right = self.dcel.create_twin_pair(
            site_a=arc.site, site_b=p
        )
        he_left.start_geom = start_point
        he_right.start_geom = start_point

        bp_left.edge = he_left
        bp_right.edge = he_right

        # Step 5: check for potential circle events involving the new triples.
        if left_leaf.prev is not None:
            self._check_circle_event(left_leaf.prev, left_leaf, mid_leaf, p.y)
        if right_leaf.next is not None:
            self._check_circle_event(mid_leaf, right_leaf, right_leaf.next, p.y)

    # ------------------------------------------------------------------
    # Circle event handling
    # ------------------------------------------------------------------

    def _handle_circle(self, event):
        """Process a circle event (steps 1-3 of HANDLECIRCLEEVENT).

        When three arcs converge, the middle arc disappears, a Voronoi
        vertex is created at the circumcenter, and the two breakpoints
        merge into one.  A new half-edge pair starts from the vertex.
        """
        arc = event.arc
        left_arc = arc.prev
        right_arc = arc.next

        if left_arc is None or right_arc is None:
            return

        # Invalidate false circle events from the neighbours — the
        # topology has changed so their potential events are obsolete.
        if left_arc.event is not None:
            left_arc.event.valid = False
            left_arc.event = None
        if right_arc.event is not None:
            right_arc.event.valid = False
            right_arc.event = None

        # Step 2: create the Voronoi vertex at the circumcenter.
        vertex = self.dcel.create_vertex(event.center)

        p = arc.parent

        # Walk up the tree to find the highest ancestor that also
        # references the disappearing site.  This is the other
        # breakpoint that converges at this circle event.
        highest_changed_ancestor = None
        curr = p
        if p.left == arc:
            while curr.parent is not None and curr.parent.left == curr:
                curr = curr.parent
            highest_changed_ancestor = curr.parent
        else:
            while curr.parent is not None and curr.parent.right == curr:
                curr = curr.parent
            highest_changed_ancestor = curr.parent

        he_p = p.edge
        he_hca = highest_changed_ancestor.edge if highest_changed_ancestor else None

        # Identify which half-edge belongs to the left arc's face
        # and which to the disappearing arc's face.
        he_left_face = None
        he_arc_face = None
        for he in (he_p, he_hca):
            if he is None:
                continue
            if he.site == left_arc.site:
                he_left_face = he
            elif he.site == arc.site:
                he_arc_face = he

        # Close the two converging half-edges at the new vertex by
        # setting the twin's origin (the incoming edge terminates here).
        if he_left_face is not None:
            he_left_face.twin.origin = vertex
        if he_arc_face is not None:
            he_arc_face.twin.origin = vertex

        # Remove the disappearing arc from the linked list.
        left_arc.next = right_arc
        right_arc.prev = left_arc

        # Step 1 continued: remove the internal node p from the AVL
        # tree by replacing it with its other child (the sibling of arc).
        gp = p.parent
        sib = p.right if p.left == arc else p.left
        sib.parent = gp

        if gp is None:
            self._beach.set_root(sib)
        else:
            if gp.left == p:
                gp.left = sib
            else:
                gp.right = sib

        self._beach.rebalance(gp)

        # Step 2 continued: create a new half-edge pair for the
        # surviving breakpoint between left_arc and right_arc.
        he_new_left, he_new_right = self.dcel.create_twin_pair(
            site_a=left_arc.site, site_b=right_arc.site
        )
        he_new_left.origin = vertex

        # Update the surviving breakpoint's site references and
        # assign the new half-edge.
        if highest_changed_ancestor:
            if highest_changed_ancestor.left_site == arc.site:
                highest_changed_ancestor.left_site = left_arc.site
            elif highest_changed_ancestor.right_site == arc.site:
                highest_changed_ancestor.right_site = right_arc.site
            highest_changed_ancestor.edge = he_new_left

        # Wire the next/prev pointers at the vertex so that the
        # cyclic order of half-edges around the face is correct.
        if he_left_face is not None:
            he_left_face.next = he_new_left
            he_new_left.prev = he_left_face
        if he_arc_face is not None and he_left_face is not None:
            he_arc_face.next = he_left_face.twin
            he_left_face.twin.prev = he_arc_face
        if he_arc_face is not None:
            he_new_right.next = he_arc_face.twin
            he_arc_face.twin.prev = he_new_right

        # Step 3: check for new circle events on the triples formed
        # by the left and right neighbours of the disappeared arc.
        if left_arc.prev is not None:
            self._check_circle_event(left_arc.prev, left_arc, right_arc, event.point.y)
        if right_arc.next is not None:
            self._check_circle_event(left_arc, right_arc, right_arc.next, event.point.y)

    # ------------------------------------------------------------------
    # Circle event detection
    # ------------------------------------------------------------------

    def _check_circle_event(self, left, mid, right, sweep_y):
        """Check whether three consecutive arcs produce a circle event.

        Computes the circumcenter of the three sites.  If the circle's
        lowest point (bottom_y) is above the sweep line, the event is
        ignored — it will be handled when the sweep line reaches it.
        Uses a cross-product test to filter out divergent triples:
        only clockwise triples produce a converging circle event.
        """
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

        # Cross product of vectors (mid-left) and (right-mid).
        # Negative = clockwise turn = the breakpoints converge.
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

    # ------------------------------------------------------------------
    # Post-processing: bounding box and face construction
    # ------------------------------------------------------------------

    def _attach_to_bounding_box(self):
        """Clip all unbounded half-edges to a large bounding box.

        Fortune's algorithm produces rays for edges that extend to
        infinity (those with no circle event at one or both ends).
        This method computes a bounding box that contains all sites
        and Voronoi vertices, then ray-casts each unbounded half-edge
        until it hits the box.  The intersection point is added as a
        new Vertex so that every half-edge has a valid origin.

        Three cases are handled:
          1. One end bounded, one unbounded — ray from known endpoint.
          2. Both ends unbounded — ray from the midpoint of the two sites.
          3. Both ends already bounded — skip.
        """
        xs = [pt.x for pt in self.points] + [v.point.x for v in self.dcel.vertices]
        ys = [pt.y for pt in self.points] + [v.point.y for v in self.dcel.vertices]

        margin = 1000
        min_x = min(xs) - margin
        max_x = max(xs) + margin
        min_y = min(ys) - margin
        max_y = max(ys) + margin

        box_corners = [
            Point(min_x, min_y), Point(max_x, min_y),
            Point(max_x, max_y), Point(min_x, max_y),
        ]
        for pt in box_corners:
            self.dcel.create_vertex(pt)

        for he in self.dcel.half_edges:
            if he.origin is not None and he.twin.origin is not None:
                continue

            # Direction perpendicular to the bisector (the ray direction).
            fx = he.twin.site.y - he.site.y
            fy = he.site.x - he.twin.site.x

            length = math.sqrt(fx * fx + fy * fy)
            if length > 0:
                fx /= length
                fy /= length

            # Case 1a: twin has origin, this half-edge does not.
            if he.origin is None and he.twin.origin is not None:
                known = he.twin.origin.point
                isec = self._ray_box_intersection(known, Point(-fx, -fy), box_corners)
                if isec:
                    he.origin = self.dcel.create_vertex(isec)

            # Case 1b: this half-edge has origin, twin does not.
            elif he.twin.origin is None and he.origin is not None:
                known = he.origin.point
                isec = self._ray_box_intersection(known, Point(fx, fy), box_corners)
                if isec:
                    he.twin.origin = self.dcel.create_vertex(isec)

            # Case 2: neither end bounded — start from the midpoint.
            elif he.origin is None and he.twin.origin is None:
                mx = (he.site.x + he.twin.site.x) / 2
                my = (he.site.y + he.twin.site.y) / 2
                mid = Point(mx, my)

                isec_fwd = self._ray_box_intersection(mid, Point(fx, fy), box_corners)
                isec_bwd = self._ray_box_intersection(mid, Point(-fx, -fy), box_corners)

                if isec_fwd and isec_bwd:
                    he.origin = self.dcel.create_vertex(isec_bwd)
                    he.twin.origin = self.dcel.create_vertex(isec_fwd)

    def _build_faces(self):
        """Build Face records by walking half-edge cycles.

        Traverses the half-edge list and follows each unvisited
        half-edge through its next-chain to collect all edges
        belonging to the same face.  Creates a Face for each
        unique site and sets outer_component to the start of the
        cycle.  Faces constructed earlier are reused rather than
        duplicated.
        """
        visited = set()
        for he in self.dcel.half_edges:
            if he.face is not None or he.origin is None or he in visited:
                continue
            face_site = he.site
            if face_site is None:
                continue

            # Find or create a Face for this site.
            face = None
            for f in self.dcel.faces:
                if f.site == face_site:
                    face = f
                    break
            if face is None:
                face = self.dcel.create_face(face_site)

            # Walk the entire cycle, assigning edges to this face.
            curr = he
            while curr is not None and curr.face is None and curr not in visited:
                visited.add(curr)
                curr.face = face
                if face.outer_component is None:
                    face.outer_component = curr
                curr = curr.next

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _ray_box_intersection(self, start, direction, box):
        """Find the first intersection of a ray with an axis-aligned box.

        Parameterises the ray as P = start + t * direction and finds
        the smallest positive t at which any of the four bounding
        planes (x = min_x, x = max_x, y = min_y, y = max_y) is hit.
        Returns the intersection Point, or None if no intersection
        exists (nearly zero direction component).
        """
        min_x = min(p.x for p in box)
        max_x = max(p.x for p in box)
        min_y = min(p.y for p in box)
        max_y = max(p.y for p in box)

        t_min = float('inf')
        pt = None

        if abs(direction.x) > 1e-9:
            t1 = (min_x - start.x) / direction.x
            if t1 > 1e-9 and t1 < t_min:
                t_min = t1
                pt = Point(min_x, start.y + t1 * direction.y)

            t2 = (max_x - start.x) / direction.x
            if t2 > 1e-9 and t2 < t_min:
                t_min = t2
                pt = Point(max_x, start.y + t2 * direction.y)

        if abs(direction.y) > 1e-9:
            t3 = (min_y - start.y) / direction.y
            if t3 > 1e-9 and t3 < t_min:
                t_min = t3
                pt = Point(start.x + t3 * direction.x, min_y)

            t4 = (max_y - start.y) / direction.y
            if t4 > 1e-9 and t4 < t_min:
                t_min = t4
                pt = Point(start.x + t4 * direction.x, max_y)

        return pt
