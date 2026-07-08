import math
from voronoi_lib.point import Point, circumcenter
from voronoi_lib.event import Event, SiteEvent, CircleEvent, EventQueue

from voronoi_lib.edge import DCEL
from voronoi_lib.beachline import BeachNode, BeachLine


class FortuneVoronoi:
    def __init__(self, points):
        self.points = sorted(points, key=lambda p: (-p.y, p.x))

        self.dcel = DCEL()

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

        self._attach_to_bounding_box()
        self._build_faces()
        return self.dcel

    def _handle_site(self, event):
        p = event.point

        if self._beach.is_empty():
            self._beach.set_root(BeachNode(p, is_leaf=True))
            return

        arc = self._beach.find_arc_above(p, p.y)

        if arc.event is not None:
            arc.event.valid = False
            arc.event = None

        start_y = self._beach.parabola_x(arc.site, p.y, p.x)
        start_point = Point(p.x, start_y)

        left_leaf = BeachNode(arc.site, is_leaf=True)
        mid_leaf = BeachNode(p, is_leaf=True)
        right_leaf = BeachNode(arc.site, is_leaf=True)

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

        bp_left = BeachNode(is_leaf=False)
        bp_left.left_site = arc.site
        bp_left.right_site = p

        bp_right = BeachNode(is_leaf=False)
        bp_right.left_site = p
        bp_right.right_site = arc.site

        bp_left.left = left_leaf
        left_leaf.parent = bp_left

        bp_left.right = bp_right
        bp_right.parent = bp_left

        bp_right.left = mid_leaf
        mid_leaf.parent = bp_right

        bp_right.right = right_leaf
        right_leaf.parent = bp_right

        bp_left.parent = arc.parent
        if arc.parent is None:
            self._beach.set_root(bp_left)
        else:
            if arc.parent.left == arc:
                arc.parent.left = bp_left
            else:
                arc.parent.right = bp_left

        self._beach.rebalance(bp_left)

        # Create twin half-edges (Step 4 of HANDLESITEEVENT)
        he_left, he_right = self.dcel.create_twin_pair(
            site_a=arc.site, site_b=p
        )
        he_left.start_geom = start_point
        he_right.start_geom = start_point

        bp_left.edge = he_left
        bp_right.edge = he_right

        if left_leaf.prev is not None:
            self._check_circle_event(left_leaf.prev, left_leaf, mid_leaf, p.y)

        if right_leaf.next is not None:
            self._check_circle_event(mid_leaf, right_leaf, right_leaf.next, p.y)

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

        # Step 2 of HANDLECIRCLEEVENT: add vertex record
        vertex = self.dcel.create_vertex(event.center)

        p = arc.parent

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

        # Identify the two converging half-edges
        he_p = p.edge
        he_hca = highest_changed_ancestor.edge if highest_changed_ancestor else None

        # Determine which half-edge belongs to which face
        he_left_face = None
        he_arc_face = None

        for he in (he_p, he_hca):
            if he is None:
                continue
            if he.site == left_arc.site:
                he_left_face = he
            elif he.site == arc.site:
                he_arc_face = he

        # Close old half-edges at the vertex (their END is at vertex)
        if he_left_face is not None:
            he_left_face.twin.origin = vertex
        if he_arc_face is not None:
            he_arc_face.twin.origin = vertex

        left_arc.next = right_arc
        right_arc.prev = left_arc

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

        # Create new twin half-edges for the new breakpoint (Step 2)
        he_new_left, he_new_right = self.dcel.create_twin_pair(
            site_a=left_arc.site, site_b=right_arc.site
        )
        he_new_left.origin = vertex

        if highest_changed_ancestor:
            if highest_changed_ancestor.left_site == arc.site:
                highest_changed_ancestor.left_site = left_arc.site
            elif highest_changed_ancestor.right_site == arc.site:
                highest_changed_ancestor.right_site = right_arc.site
            highest_changed_ancestor.edge = he_new_left

        # Set next/prev pointers at the vertex
        if he_left_face is not None:
            he_left_face.next = he_new_left
            he_new_left.prev = he_left_face
        if he_arc_face is not None and he_left_face is not None:
            he_arc_face.next = he_left_face.twin
            he_left_face.twin.prev = he_arc_face
        if he_arc_face is not None:
            he_new_right.next = he_arc_face.twin
            he_arc_face.twin.prev = he_new_right

        # Check new triples
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

    def _attach_to_bounding_box(self):
        if self.dcel.vertices:
            xs = [v.point.x for v in self.dcel.vertices]
            ys = [v.point.y for v in self.dcel.vertices]
        else:
            xs = [pt.x for pt in self.points]
            ys = [pt.y for pt in self.points]
        margin = 1000
        min_x = min(xs) - margin
        max_x = max(xs) + margin
        min_y = min(ys) - margin
        max_y = max(ys) + margin

        box_corners = [
            Point(min_x, min_y), Point(max_x, min_y),
            Point(max_x, max_y), Point(min_x, max_y),
        ]
        box_vertices = []
        for pt in box_corners:
            v = self.dcel.create_vertex(pt)
            box_vertices.append(v)

        for he in self.dcel.half_edges:
            if he.origin is not None and he.twin.origin is not None:
                continue

            dx = he.twin.site.x - he.site.x
            dy = he.twin.site.y - he.site.y
            nx = -dy
            ny = dx
            length = math.sqrt(nx * nx + ny * ny)
            if length > 0:
                nx /= length
                ny /= length
            dir_pt = Point(nx, ny)

            if he.origin is None and he.twin.origin is not None:
                known = he.twin.origin.point
                test_pt = Point(known.x - nx * 10000, known.y - ny * 10000)
                dist_test = (test_pt.x - he.site.x) ** 2 + (test_pt.y - he.site.y) ** 2
                dist_known = (known.x - he.site.x) ** 2 + (known.y - he.site.y) ** 2
                if dist_test < dist_known:
                    nx, ny = -nx, -ny
                isec = self._ray_box_intersection(known, Point(nx, ny), box_corners)
                if isec:
                    he.origin = self.dcel.create_vertex(isec)

            elif he.twin.origin is None and he.origin is not None:
                known = he.origin.point
                test_pt = Point(known.x + nx * 10000, known.y + ny * 10000)
                dist_test = (test_pt.x - he.site.x) ** 2 + (test_pt.y - he.site.y) ** 2
                dist_known = (known.x - he.site.x) ** 2 + (known.y - he.site.y) ** 2
                if dist_test < dist_known:
                    nx, ny = -nx, -ny
                isec = self._ray_box_intersection(known, Point(nx, ny), box_corners)
                if isec:
                    he.twin.origin = self.dcel.create_vertex(isec)

            elif he.origin is None and he.twin.origin is None:
                mx = (he.site.x + he.twin.site.x) / 2
                my = (he.site.y + he.twin.site.y) / 2
                mid = Point(mx, my)
                half_edge_dir = Point(nx, ny)
                isec1 = self._ray_box_intersection(mid, half_edge_dir, box_corners)
                isec2 = self._ray_box_intersection(mid, Point(-nx, -ny), box_corners)
                if isec1 and isec2:
                    he.origin = self.dcel.create_vertex(isec1)
                    he.twin.origin = self.dcel.create_vertex(isec2)

    def _build_faces(self):
        visited = set()
        for he in self.dcel.half_edges:
            if he.face is not None or he.origin is None or he in visited:
                continue
            face_site = he.site
            if face_site is None:
                continue

            face = None
            for f in self.dcel.faces:
                if f.site == face_site:
                    face = f
                    break
            if face is None:
                face = self.dcel.create_face(face_site)

            curr = he
            while curr is not None and curr.face is None and curr not in visited:
                visited.add(curr)
                curr.face = face
                if face.outer_component is None:
                    face.outer_component = curr
                curr = curr.next

    def _ray_box_intersection(self, start, direction, box):
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
