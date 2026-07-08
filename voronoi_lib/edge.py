from voronoi_lib.point import Point


class Vertex:
    def __init__(self, point):
        self.point = point
        self.incident_edge = None

    def __repr__(self):
        return f"V({self.point.x:.2f} {self.point.y:.2f})"


class HalfEdge:
    def __init__(self, site=None):
        self.origin = None
        self.twin = None
        self.face = None
        self.next = None
        self.prev = None
        self.site = site
        self.start_geom = None

    @property
    def end(self):
        return self.twin.origin.point if self.twin and self.twin.origin else None

    def __repr__(self):
        o = f"({self.origin.point.x:.1f},{self.origin.point.y:.1f})" if self.origin else "None"
        e = f"({self.end.x:.1f},{self.end.y:.1f})" if self.end else "None"
        return f"HE({o}->{e}, site={self.site})"


class Face:
    def __init__(self, site):
        self.site = site
        self.outer_component = None

    def vertices(self):
        verts = []
        if not self.outer_component:
            return verts
        he = self.outer_component
        while True:
            if he.origin:
                verts.append(he.origin.point)
            he = he.next
            if he is self.outer_component:
                break
        return verts

    def __repr__(self):
        return f"Face(site=({self.site.x:.1f},{self.site.y:.1f}))"


class DCEL:
    def __init__(self):
        self.vertices = []
        self.half_edges = []
        self.faces = []

    def create_vertex(self, point):
        for v in self.vertices:
            if abs(v.point.x - point.x) < 1e-9 and abs(v.point.y - point.y) < 1e-9:
                return v
        v = Vertex(point)
        self.vertices.append(v)
        return v

    def create_half_edge(self, site=None):
        he = HalfEdge(site)
        self.half_edges.append(he)
        return he

    def create_twin_pair(self, site_a, site_b):
        he_a = self.create_half_edge(site=site_a)
        he_b = self.create_half_edge(site=site_b)
        he_a.twin = he_b
        he_b.twin = he_a
        return he_a, he_b

    def create_face(self, site):
        f = Face(site)
        self.faces.append(f)
        return f
