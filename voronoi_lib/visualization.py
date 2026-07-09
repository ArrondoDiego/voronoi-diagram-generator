"""Matplotlib-based visualization for the Voronoi diagram."""

import matplotlib.pyplot as plt


def save_image(points, cells, clip_box, filename="voronoi.png"):
    """Render the Voronoi diagram and save it as a PNG image.

    Args:
        points: List of site Points (shown as red markers).
        cells: Dict mapping site -> list of Points (the clipped cell polygon).
        clip_box: List of four Points defining the display boundary.
        filename: Output path for the PNG image.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    min_x = min(p.x for p in clip_box)
    max_x = max(p.x for p in clip_box)
    min_y = min(p.y for p in clip_box)
    max_y = max(p.y for p in clip_box)

    ax.set_xlim(min_x - 5, max_x + 5)
    ax.set_ylim(min_y - 5, max_y + 5)

    colors = ['#f4f1de', '#e07a5f', '#3d5a80', '#98c1d9', '#ee6c4d', '#293241', '#81b29a']

    for i, (site, clipped_vertices) in enumerate(cells.items()):
        if not clipped_vertices:
            continue

        xs = [pt.x for pt in clipped_vertices]
        ys = [pt.y for pt in clipped_vertices]

        color = colors[i % len(colors)]
        ax.fill(xs, ys, color=color, alpha=0.6, edgecolor='#2b2d42', linewidth=1.5)

    site_xs = [p.x for p in points]
    site_ys = [p.y for p in points]
    ax.scatter(site_xs, site_ys, color='#d90429', zorder=5, s=40, label='Sites (Seeds)')

    ax.set_title("Voronoi Diagram", fontsize=14, fontweight='bold', pad=15)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"\nImage saved as: {filename}")
    plt.close()
