# Voronoi Diagram Generator

A pure Python implementation of **Fortune's algorithm** (sweep-line) for computing Voronoi diagrams in O(n log n).

The output is a full **DCEL** (Doubly-Connected Edge List) with **Vertex**, **HalfEdge**, and **Face** records,
faithfully following the algorithm description in `docs/algorithm.md` (de Berg et al., "Computational Geometry").

## Dependencies

- Python 3.10+
- `matplotlib` (only for visualization/GUI)

```bash
pip install matplotlib
```

## Usage

```bash
# CLI — prompts for 5 points, saves voronoi_output.png
python main.py

# Interactive — click to place seeds, then press "Compute Voronoi"
python interactive.py
```
