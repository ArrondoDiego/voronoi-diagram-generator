# Voronoi Diagram generator — Fortune's algorithm

A pure Python implementation of **Fortune's sweepline algorithm** (de Berg et al., *Computational Geometry*, Chapter 7)
for computing Voronoi diagrams in **O(n log n)** time.

The output is returned as a **DCEL** (Doubly-Connected Edge List) with `Vertex`, `HalfEdge`, and `Face` records,
faithfully following the pseudocode in `docs/algorithm.md`.

## Project structure

```
voronoi_lib/              # Core library (Fortune's algorithm)
├── __init__.py           # Package exports: FortuneVoronoi, Point
├── point.py              # Point class + circumcenter (Cramer's rule)
├── event.py              # SiteEvent, CircleEvent, EventQueue (heap)
├── edge.py               # DCEL: Vertex, HalfEdge, Face
├── beachline.py          # Beach line status structure (AVL tree)
├── fortune.py            # Main algorithm: FortuneVoronoi.compute()
├── utils.py              # extract_cells — DCEL → cell polygons
├── clipping.py           # Sutherland–Hodgman polygon clipping
└── visualization.py      # matplotlib rendering (save_image)

main.py                   # Interactive GUI (click to add, compute Voronoi)
docs/
├── algorithm.md          # Pseudocode reference (de Berg et al.)
├── theory.pdf            # Supporting theory slides
└── presentation.pdf      # Exam presentation slides
```

## Dependencies

- Python 3.10+
- `matplotlib` (for the interactive GUI)

```bash
pip install matplotlib
```

## Usage

```bash
# Interactive GUI — click to place sites, then press "Compute Voronoi"
python main.py
```
