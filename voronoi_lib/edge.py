"""DCEL (Doubly-Connected Edge List) data structure.

The DCEL is the standard representation for planar subdivisions used
in computational geometry.  It stores the Voronoi diagram as a set of
vertices, half-edges, and faces with explicit adjacency pointers.
"""

from voronoi_lib.point import Point


class Vertex:
    """A vertex in the planar subdivision (a Voronoi vertex or bounding-box corner).

    Attributes:
        point: The geometric location of this vertex.
        incident_edge: One of the half-edges that has this vertex as its origin.
                       (Currently unused; maintained for DCEL completeness.)
    """

    def __init__(self, point):
        self.point = point
        self.incident_edge = None

    def __repr__(self):
        return f"V({self.point.x:.2f} {self.point.y:.2f})"


class HalfEdge:
    """A directed edge in the DCEL.

    Each undirected Voronoi edge is represented by a pair of twin half-edges
    pointing in opposite directions, each belonging to the face of one adjacent site.

    Attributes:
        origin: The Vertex at the start of this half-edge.
        twin: The opposite-direction half-edge (same geometric line).
        face: The Face (Voronoi cell) on this side of the edge.
        next: The next half-edge in the cyclic order around the face.
        prev: The previous half-edge in the cyclic order around the face.
        site: The site whose cell this half-edge bounds.
        start_geom: Temporary starting point for the edge during construction.
    """

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
        """The point at the end of this half-edge (origin of the twin)."""
        return self.twin.origin.point if self.twin and self.twin.origin else None

    def __repr__(self):
        o = f"({self.origin.point.x:.1f},{self.origin.point.y:.1f})" if self.origin else "None"
        e = f"({self.end.x:.1f},{self.end.y:.1f})" if self.end else "None"
        return f"HE({o}->{e}, site={self.site})"


class Face:
    """A face of the DCEL representing one Voronoi cell.

    Attributes:
        site: The site whose Voronoi cell this face represents.
        outer_component: A half-edge on the boundary of this face.
    """

    def __init__(self, site):
        self.site = site
        self.outer_component = None

    def vertices(self):
        """Walk the boundary and collect all vertices of this face."""
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
    """Doubly-Connected Edge List for the Voronoi diagram.

    Maintains three lists (vertices, half_edges, faces) and provides
    factory methods to create components with deduplication.
    """

    def __init__(self):
        self.vertices = []
        self.half_edges = []
        self.faces = []

    def create_vertex(self, point):
        """Create or reuse a Vertex at the given location.

        Returns the existing vertex if one already exists within epsilon
        of the given point, preventing duplicate geometry.
        """
        for v in self.vertices:
            if abs(v.point.x - point.x) < 1e-9 and abs(v.point.y - point.y) < 1e-9:
                return v
        v = Vertex(point)
        self.vertices.append(v)
        return v

    def create_half_edge(self, site=None):
        """Create a new half-edge belonging to the given site and append it."""
        he = HalfEdge(site)
        self.half_edges.append(he)
        return he

    def create_twin_pair(self, site_a, site_b):
        """Create a pair of twin half-edges for an edge between two sites.

        One half-edge belongs to site_a's face, the other to site_b's face.
        Returns (he_a, he_b).
        """
        he_a = self.create_half_edge(site=site_a)
        he_b = self.create_half_edge(site=site_b)
        he_a.twin = he_b
        he_b.twin = he_a
        return he_a, he_b

    def create_face(self, site):
        """Create a new Face for the given site and append it."""
        f = Face(site)
        self.faces.append(f)
        return f
