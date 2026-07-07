import math
from voronoi_lib.point import Point, circumcenter
from voronoi_lib.event import Event, SiteEvent, CircleEvent, EventQueue

from voronoi_lib.edge import VoronoiEdge
from voronoi_lib.beachline import BeachNode, BeachLine

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
            self._beach.set_root(BeachNode(p, is_leaf=True))
            return

        # Ricerca binaria sull'albero
        arc = self._beach.find_arc_above(p, p.y)

        if arc.event is not None:
            arc.event.valid = False
            arc.event = None

        start_y = self._beach.parabola_x(arc.site, p.y, p.x)
        start_point = Point(p.x, start_y)

        # 1. Crea le nuove foglie (archi)
        left_leaf = BeachNode(arc.site, is_leaf=True)
        mid_leaf = BeachNode(p, is_leaf=True)
        right_leaf = BeachNode(arc.site, is_leaf=True)

        # Mantieni i puntatori orizzontali solo sulle foglie per i cerchi in O(1)
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

        # 2. Crea i nodi interni (i due nuovi breakpoint associati)
        bp_left = BeachNode(is_leaf=False)
        bp_left.left_site = arc.site
        bp_left.right_site = p

        bp_right = BeachNode(is_leaf=False)
        bp_right.left_site = p
        bp_right.right_site = arc.site

        # 3. Assembla il sottoalbero locale
        bp_left.left = left_leaf
        left_leaf.parent = bp_left

        bp_left.right = bp_right
        bp_right.parent = bp_left

        bp_right.left = mid_leaf
        mid_leaf.parent = bp_right

        bp_right.right = right_leaf
        right_leaf.parent = bp_right

        # 4. Sostituisci la vecchia foglia 'arc' con il nuovo sottoalbero nell'albero principale
        bp_left.parent = arc.parent
        if arc.parent is None:
            self._beach.set_root(bp_left)
        else:
            if arc.parent.left == arc:
                arc.parent.left = bp_left
            else:
                arc.parent.right = bp_left

        # NUOVO: Ripristina le invarianti AVL
        self._beach.rebalance(bp_left)

        # 5. Generazione dei segmenti geometrici
        edge1 = VoronoiEdge(start_point, arc.site, p)
        edge2 = VoronoiEdge(start_point, p, arc.site)
        self.edges.append(edge1)
        self.edges.append(edge2)

        bp_left.edge = edge1
        bp_right.edge = edge2

        # Verifica i potenziali Circle Event usando la catena di foglie orizzontali
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

        vertex = event.center
        self.vertices.append(vertex)

        p = arc.parent
        
        # Cerca l'altro breakpoint nell'albero che collassa in questo medesimo vertice
        highest_changed_ancestor = None
        curr = p
        while curr.parent is not None:
            if curr.parent.left_site == arc.site or curr.parent.right_site == arc.site:
                highest_changed_ancestor = curr.parent
                break
            curr = curr.parent

        # Chiudi i vecchi spigoli nel vertice calcolato
        if p.edge is not None:
            p.edge.end = vertex
        if highest_changed_ancestor and highest_changed_ancestor.edge is not None:
            highest_changed_ancestor.edge.end = vertex

        # Sgancia la foglia dalla lista orizzontale
        left_arc.next = right_arc
        right_arc.prev = left_arc

        # Rimuovi la foglia 'arc' dall'albero binario: il fratello prende il posto del padre
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

        # NUOVO: Ripristina le invarianti AVL partendo dal nonno
        self._beach.rebalance(gp)   

        # Crea il nuovo spigolo che parte dal vertice appena scoperto
        new_edge = VoronoiEdge(vertex, left_arc.site, right_arc.site)
        self.edges.append(new_edge)

        # Aggiorna il breakpoint superstite con la nuova coppia di siti confinanti
        if highest_changed_ancestor:
            if highest_changed_ancestor.left_site == arc.site:
                highest_changed_ancestor.left_site = left_arc.site
            elif highest_changed_ancestor.right_site == arc.site:
                highest_changed_ancestor.right_site = right_arc.site
            highest_changed_ancestor.edge = new_edge

        # Controlla le nuove triplette adiacenti per i prossimi circle event
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
            if edge.start is not None and edge.end is not None:
                continue # Lo spigolo è già un segmento chiuso

            # Vettore tra i due siti
            dx = edge.right.x - edge.left.x
            dy = edge.right.y - edge.left.y
            
            # Vettore ortogonale (direzione del bordo di Voronoi)
            # Dobbiamo assicurarci che punti verso l'esterno (verso il basso/l'infinito)
            nx = -dy
            ny = dx

            # Normalizziamo il vettore direzione (opzionale ma consigliato per consistenza)
            length = math.sqrt(nx * nx + ny * ny)
            if length > 0:
                nx /= length
                ny /= length

            edge.direction = Point(nx, ny)