import math
from voronoi_lib.point import Point 

class BeachNode:
    def __init__(self, site=None, is_leaf=False):
        self.is_leaf = is_leaf
        self.parent = None
        self.left = None
        self.right = None
        
        # NEW: Properties for AVL balancing
        self.height = 1  
        
        # Attributes for Leaves (Actual Arcs)
        self.site = site
        self.event = None  
        self.prev = None   
        self.next = None   
        
        # Attributes for Internal Nodes (Breakpoints)
        self.left_site = None
        self.right_site = None
        self.edge = None
        
    def __repr__(self):
        if self.is_leaf:
            return f"Leaf({self.site})"
        return f"Breakpoint(<{self.left_site}, {self.right_site}>)"


class BeachLine:
    def __init__(self):
        self._root = None

    @property
    def root(self):
        return self._root

    def set_root(self, node):
        self._root = node

    def is_empty(self):
        return self._root is None

    def parabola_x(self, site, directrix_y, x_query):
        if abs(site.y - directrix_y) < 1e-9:
            return -float('inf')
        return (x_query - site.x)**2 / (2 * (site.y - directrix_y)) + (site.y + directrix_y) / 2

    def find_arc_above(self, point, sweep_y):
        if self._root is None:
            return None

        node = self._root
        # Descend the tree until finding a leaf
        while not node.is_leaf:
            bps = self.get_breakpoints(node.left_site, node.right_site, sweep_y)
            if bps is None:
                return node

            # Select the active breakpoint based on relative site heights
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
        p1, p2 = left, right
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
    def update_height(self, node):
        if node:
            hl = node.left.height if node.left else 0
            hr = node.right.height if node.right else 0
            node.height = 1 + max(hl, hr)

    def balance_factor(self, node):
        if not node: return 0
        hl = node.left.height if node.left else 0
        hr = node.right.height if node.right else 0
        return hl - hr

    def _rotate_left(self, z):
        y = z.right
        T2 = y.left

        # Perform the rotation
        y.left = z
        z.right = T2

        # Update 'parent' pointers
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

        # Update heights
        self.update_height(z)
        self.update_height(y)
        return y

    def _rotate_right(self, z):
        y = z.left
        T3 = y.right

        # Perform the rotation
        y.right = z
        z.left = T3

        # Update 'parent' pointers
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

        # Update heights
        self.update_height(z)
        self.update_height(y)
        return y

    def rebalance(self, node):
        """Rebalances tree from given node up to root, rotating where necessary."""
        while node is not None:
            self.update_height(node)
            bf = self.balance_factor(node)

            # Case Left Left
            if bf > 1 and self.balance_factor(node.left) >= 0:
                node = self._rotate_right(node)
            # Case Right Right
            elif bf < -1 and self.balance_factor(node.right) <= 0:
                node = self._rotate_left(node)
            # Case Left Right
            elif bf > 1 and self.balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
                node = self._rotate_right(node)
            # Case Right Left
            elif bf < -1 and self.balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
                node = self._rotate_left(node)

            node = node.parent