import math
import random
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from voronoi_lib.point import Point
from voronoi_lib.fortune import FortuneVoronoi
from voronoi_lib.clipping import clip_polygon
from collections import defaultdict
from voronoi_lib.utils import extract_cells




class VoronoiGUI:
    def __init__(self):
        self.points = []
        self.computed = False
        self.box = [Point(0, 0), Point(100, 0), Point(100, 100), Point(0, 100)]
        self.colors = ['#f4f1de', '#e07a5f', '#3d5a80', '#98c1d9', '#ee6c4d', '#293241', '#81b29a']

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        plt.subplots_adjust(bottom=0.20)

        self._setup_axes()

        ax_reset = plt.axes([0.15, 0.05, 0.2, 0.075])
        self.btn_reset = Button(ax_reset, 'Reset')

        ax_random = plt.axes([0.40, 0.05, 0.2, 0.075])
        self.btn_random = Button(ax_random, '+5 Random Points')

        ax_compute = plt.axes([0.65, 0.05, 0.2, 0.075])
        self.btn_compute = Button(ax_compute, 'Compute Voronoi')

        self.fig.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        self.btn_compute.on_clicked(self.on_compute_click)
        self.btn_reset.on_clicked(self.on_reset_click)
        self.btn_random.on_clicked(self.on_random_click)

    def _setup_axes(self):
        self.ax.set_title("Click, use Random Points, or press 'Compute'", fontsize=12)
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle='--', alpha=0.5)

    def on_canvas_click(self, event):
        if self.computed or event.inaxes != self.ax:
            return

        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            self.points.append(Point(x, y))
            self.ax.scatter([x], [y], color='#d90429', zorder=5, s=40)
            self.fig.canvas.draw()

    def on_random_click(self, event):
        if self.computed:
            return

        for _ in range(5):
            x, y = random.uniform(10, 90), random.uniform(10, 90)
            self.points.append(Point(x, y))
            self.ax.scatter([x], [y], color='#d90429', zorder=5, s=40)

        self.fig.canvas.draw()

    def on_reset_click(self, event):
        self.points = []
        self.computed = False

        self.ax.clear()
        self._setup_axes()
        self.fig.canvas.draw()

    def on_compute_click(self, event):
        if self.computed or len(self.points) < 2:
            print("Insert at least 2 points")
            return

        self.computed = True
        self.fig.canvas.draw()

        # Define the infinite domain
        universe_box = [
            Point(-10000, -10000), Point(10000, -10000), 
            Point(10000, 10000), Point(-10000, 10000)
        ]

        # Mathematical execution without dummy data
        v = FortuneVoronoi(self.points)
        edges = v.compute()
        
        # Extraction passing real sites for vectorial self-verification
        cells = extract_cells(edges, universe_box, self.points)

        # Rendering and Clipping for the screen (0-100)
        for i, (site, vertices) in enumerate(cells.items()):
            clipped_vertices = clip_polygon(vertices, self.box)
            if not clipped_vertices:
                continue

            xs = [pt.x for pt in clipped_vertices]
            ys = [pt.y for pt in clipped_vertices]

            color = self.colors[i % len(self.colors)]
            self.ax.fill(xs, ys, color=color, alpha=0.6, edgecolor='#2b2d42', linewidth=1.5)

        self.ax.set_title("Voronoi Diagram", fontsize=14, fontweight='bold')
        self.fig.canvas.draw()

def main():
    gui = VoronoiGUI()
    plt.show()


if __name__ == "__main__":
    main()
