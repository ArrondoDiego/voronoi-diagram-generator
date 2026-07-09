"""Fortune's algorithm for Voronoi diagram construction.

This package implements Fortune's sweepline algorithm (de Berg et al.)
to compute the Voronoi diagram of a set of point sites in O(n log n) time.
The result is returned as a DCEL (Doubly-Connected Edge List).
"""

from voronoi_lib.fortune import FortuneVoronoi
from voronoi_lib.point import Point

__all__ = ["FortuneVoronoi", "Point"]
