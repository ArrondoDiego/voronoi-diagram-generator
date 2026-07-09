"""Beach line status structure for Fortune's algorithm.

The beach line is the central data structure that maintains the ordered
sequence of parabolic arcs between the sweep line and the processed region.
It is stored as an AVL tree where:
  - Leaves  represent parabolic arcs (each storing a site).
  - Internal nodes represent breakpoints between adjacent arcs.

The AVL property ensures O(log n) for all operations: search, split, merge.
"""

import math
from voronoi_lib.point import Point


class BeachNode:
    """A node in the beach line AVL tree.

    Can be either a leaf (arc) or an internal node (breakpoint).
    Different fields are used depending on the node type to avoid
    subclass overhead.

    Attributes (common):
        is_leaf: True for arc nodes, False for breakpoint nodes.
        parent: Parent node in the AVL tree.
        left: Left child in the AVL tree.
        right: Right child in the AVL tree.
        height: Subtree height for AVL balancing.

    Leaf attributes (arcs):
        site: The site that generates this parabolic arc.
        event: Pointer to a pending CircleEvent for this arc (if any).
        prev: Previous leaf in the doubly-linked arc sequence.
        next: Next leaf in the doubly-linked arc sequence.

    Internal attributes (breakpoints):
        left_site, right_site: The two sites whose bisector this
            breakpoint traces out.
        edge: The HalfEdge being traced by this breakpoint.
    """

    def __init__(self, site=None, is_leaf=False):
        self.is_leaf = is_leaf
        self.parent = None
        self.left = None
        self.right = None

        self.height = 1

        # leaf attributes (arcs)
        self.site = site
        self.event = None
        self.prev = None
        self.next = None

        # internal attributes (breakpoints)
        self.left_site = None
        self.right_site = None
        self.edge = None

    def __repr__(self):
        if self.is_leaf:
            return f"Leaf({self.site})"
        return f"Breakpoint(<{self.left_site}, {self.right_site}>)"


class BeachLine:
    """AVL-tree implementation of the beach line status structure.

    Maintains the ordered sequence of parabolic arcs created by the
    intersection of each site's distance function with the current
    sweep line position.  Supports O(log n) arc lookup and tree
    rebalancing after insertions and deletions.
    """

    def __init__(self):
        self._root = None

    @property
    def root(self):
        return self._root

    def set_root(self, node):
        """Set the root of the AVL tree."""
        self._root = node

    def is_empty(self):
        """Check whether the beach line has any arcs."""
        return self._root is None

    def parabola_x(self, site, directrix_y, x_query):
        """Compute the y-coordinate of a parabola on the beach line.

        For a site at (sx, sy) and directrix at y = d, the parabola
        is defined as all points equidistant from the site and the
        directrix.  This method returns the y-value for a given x.
        Returns -inf when the site lies on the directrix (the
        parabola degenerates to a vertical line).
        """
        if abs(site.y - directrix_y) < 1e-9:
            return -float('inf')
        return (x_query - site.x)**2 / (2 * (site.y - directrix_y)) + (site.y + directrix_y) / 2

    def find_arc_above(self, point, sweep_y):
        """Find the leaf (arc) directly above the given point.

        Performs a binary search on the breakpoints: at each internal
        node, the x-coordinate of the active breakpoint determines
        whether to descend left or right.  Returns the leaf node
        whose arc covers the point's x-coordinate.
        """
        if self._root is None:
            return None

        node = self._root
        while not node.is_leaf:
            bps = self.get_breakpoints(node.left_site, node.right_site, sweep_y)
            if bps is None:
                return node

            # When the two sites have different y-coordinates the
            # parabola intersection produces two breakpoints (one
            # per branch). Select the one relevant at this sweep
            # position based on which site is higher.
            if node.left_site.y < node.right_site.y:
                active_bp = bps[1]
            else:
                active_bp = bps[0]

            if point.x < active_bp:
                node = node.left
            else:
                node = node.right
        return node

    def get_breakpoints(self, left, right, sweep_y):
        """Compute the x-coordinate(s) of the breakpoint between two sites.

        The breakpoint of two parabolas is the solution to the equation
        derived from equating their distance functions.  The quadratic
        can produce two roots (one on each side); which one is active
        depends on the relative site heights.

        Handles degenerate cases: both sites on the directrix, one site
        on the directrix, and coincident parabolas (a ≈ 0).
        """
        p1, p2 = left, right
        d = sweep_y

        # Both sites on the directrix — the perpendicular bisector
        # is vertical at the midpoint.
        if abs(p1.y - d) < 1e-9 and abs(p2.y - d) < 1e-9:
            x = (p1.x + p2.x) / 2
            return (x, x)

        # One site on the directrix — the parabola degenerates to a
        # vertical ray from that site's x-coordinate.
        if abs(p1.y - d) < 1e-9:
            x = p1.x
            return (x, x)
        if abs(p2.y - d) < 1e-9:
            x = p2.x
            return (x, x)

        a = 1 / (p1.y - d) - 1 / (p2.y - d)

        # Nearly coincident parabolas — the breakpoint is near
        # the midpoint.
        if abs(a) < 1e-9:
            x = (p1.x + p2.x) / 2
            return (x, x)

        b = -2 * p1.x / (p1.y - d) + 2 * p2.x / (p2.y - d)
        c = (p1.x**2 + p1.y**2 - d**2) / (p1.y - d) - (p2.x**2 + p2.y**2 - d**2) / (p2.y - d)

        disc = b * b - 4 * a * c
        if disc < 0:
            # Floating-point error may produce a tiny negative
            # discriminant when the true value is zero.
            if disc > -1e-9:
                disc = 0
            else:
                return None

        x1 = (-b - math.sqrt(disc)) / (2 * a)
        x2 = (-b + math.sqrt(disc)) / (2 * a)
        return (x1, x2) if x1 < x2 else (x2, x1)

    # ------------------------------------------------------------------
    # AVL tree balancing
    # ------------------------------------------------------------------

    def update_height(self, node):
        """Recalculate the height of a node from its children's heights."""
        if node:
            hl = node.left.height if node.left else 0
            hr = node.right.height if node.right else 0
            node.height = 1 + max(hl, hr)

    def balance_factor(self, node):
        """Return the AVL balance factor (left height - right height)."""
        if not node:
            return 0
        hl = node.left.height if node.left else 0
        hr = node.right.height if node.right else 0
        return hl - hr

    def _rotate_left(self, z):
        """Left rotation around node z (right child becomes new root)."""
        y = z.right
        T2 = y.left

        y.left = z
        z.right = T2

        y.parent = z.parent
        if z.parent is None:
            self._root = y
        elif z.parent.left == z:
            z.parent.left = y
        else:
            z.parent.right = y

        z.parent = y
        if T2:
            T2.parent = z

        self.update_height(z)
        self.update_height(y)
        return y

    def _rotate_right(self, z):
        """Right rotation around node z (left child becomes new root)."""
        y = z.left
        T3 = y.right

        y.right = z
        z.left = T3

        y.parent = z.parent
        if z.parent is None:
            self._root = y
        elif z.parent.left == z:
            z.parent.left = y
        else:
            z.parent.right = y

        z.parent = y
        if T3:
            T3.parent = z

        self.update_height(z)
        self.update_height(y)
        return y

    def rebalance(self, node):
        """Walk up from node to root, updating heights and rotating as needed.

        Applies the four standard AVL rebalancing cases:
          Left-Left, Right-Right, Left-Right, Right-Left.
        """
        while node is not None:
            self.update_height(node)
            bf = self.balance_factor(node)

            # Left-Left case
            if bf > 1 and self.balance_factor(node.left) >= 0:
                node = self._rotate_right(node)
            # Right-Right case
            elif bf < -1 and self.balance_factor(node.right) <= 0:
                node = self._rotate_left(node)
            # Left-Right case
            elif bf > 1 and self.balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
                node = self._rotate_right(node)
            # Right-Left case
            elif bf < -1 and self.balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
                node = self._rotate_left(node)

            node = node.parent
