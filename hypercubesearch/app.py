"""
Hypercube Search Explorer — PySide6 application
=================================================

An interactive desktop app for visualizing BFS, DFS, and A* search over an
n-dimensional hypercube graph, rendered as a rotatable 3D projection.
Everything renders live in the window — nothing is written to disk.

Run:
    python hypercube_app.py

Requires: PySide6, matplotlib
"""

import sys

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Line3DCollection

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QStatusBar, QRadioButton, QButtonGroup,
    QGroupBox,
)

from core import ALGORITHMS, build_hypercube, layout_positions_3d, run_experiment

MAX_GRAPH_DIM = 10   # 1024 states / 5120 edges — still smooth to rotate
MAX_SCALING_DIM = 16


# ---------------------------------------------------------------------------
# Background workers (keep the UI responsive for larger dimensions)
# ---------------------------------------------------------------------------

class GraphWorker(QThread):
    done = Signal(dict, dict, str, str)  # results, positions, start, goal

    def __init__(self, n):
        super().__init__()
        self.n = n

    def run(self):
        graph = build_hypercube(self.n)
        start, goal = "0" * self.n, "1" * self.n
        positions = layout_positions_3d(self.n)
        results = {}
        for name, algo in ALGORITHMS.items():
            path, order = algo(graph, start, goal)
            results[name] = {"graph": graph, "path": path, "order": order}
        self.done.emit(results, positions, start, goal)


class ScalingWorker(QThread):
    done = Signal(list)

    def __init__(self, max_dim):
        super().__init__()
        self.max_dim = max_dim

    def run(self):
        self.done.emit(run_experiment(self.max_dim))


# ---------------------------------------------------------------------------
# Tab 1: Graph explorer (3D, rotatable, one algorithm at a time)
# ---------------------------------------------------------------------------

class GraphExplorerTab(QWidget):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        self.worker = None
        self.cached_results = None
        self.cached_positions = None
        self.cached_start = None
        self.cached_goal = None
        self.cached_n = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(16)
        controls.addWidget(QLabel("Dimension (n):"))
        self.dim_spin = QSpinBox()
        self.dim_spin.setRange(2, MAX_GRAPH_DIM)
        self.dim_spin.setValue(4)
        controls.addWidget(self.dim_spin)
        self.run_btn = QPushButton("Run search")
        self.run_btn.clicked.connect(self.run_search)
        controls.addWidget(self.run_btn)

        controls.addSpacing(24)
        algo_box = QGroupBox("Show algorithm")
        algo_layout = QHBoxLayout(algo_box)
        algo_layout.setSpacing(16)
        self.algo_group = QButtonGroup(self)
        self.algo_buttons = {}
        for i, name in enumerate(ALGORITHMS):
            btn = QRadioButton(name)
            if i == 0:
                btn.setChecked(True)
            btn.toggled.connect(self._on_algo_toggled)
            self.algo_group.addButton(btn)
            algo_layout.addWidget(btn)
            self.algo_buttons[name] = btn
        controls.addWidget(algo_box)

        controls.addStretch()
        layout.addLayout(controls)

        self.info_label = QLabel(" ")
        self.info_label.setStyleSheet("font-size: 13px; color: #444; padding: 2px 4px;")
        layout.addWidget(self.info_label)

        self.figure = Figure(figsize=(9, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")
        layout.addWidget(self.canvas, stretch=1)

        hint = QLabel("Drag to rotate \u00b7 scroll to zoom")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(hint)

        legend_elems = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#1D9E75', markersize=10, label='start'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#D85A30', markersize=10, label='goal'),
            Line2D([0], [0], color='#D85A30', linewidth=3, label='reconstructed path'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#378ADD', markersize=9, label='visited'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='0.8', markersize=9, label='unvisited'),
        ]
        self.figure.legend(handles=legend_elems, loc='lower center', ncol=5, fontsize=10, frameon=False)
        self.figure.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.08)

        self.run_search()

    def _on_algo_toggled(self, checked):
        if checked and self.cached_results is not None:
            self.render_selected()

    def selected_algorithm(self):
        for name, btn in self.algo_buttons.items():
            if btn.isChecked():
                return name
        return next(iter(ALGORITHMS))

    def run_search(self):
        n = self.dim_spin.value()
        self.run_btn.setEnabled(False)
        self.status_bar.showMessage(f"Running BFS / DFS / A* on the {n}-dimensional hypercube "
                                     f"({2 ** n} states)...")
        self.worker = GraphWorker(n)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_done(self, results, positions, start, goal):
        self.cached_results = results
        self.cached_positions = positions
        self.cached_start = start
        self.cached_goal = goal
        self.cached_n = self.dim_spin.value()
        self.render_selected()
        self.run_btn.setEnabled(True)
        self.status_bar.showMessage("Done.", 3000)

    def render_selected(self):
        name = self.selected_algorithm()
        data = self.cached_results[name]
        # preserve the current camera angle across redraws/selection changes
        elev, azim = self.ax.elev, self.ax.azim
        self.ax.clear()
        draw_algorithm_3d(self.ax, data["graph"], self.cached_positions,
                           self.cached_start, self.cached_goal,
                           data["path"], data["order"], name, self.cached_n)
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()
        self.info_label.setText(
            f"n = {self.cached_n}  \u00b7  {name}  \u00b7  "
            f"explored {len(data['order'])} of {2 ** self.cached_n} states  \u00b7  "
            f"path length {len(data['path']) - 1}"
        )


def draw_algorithm_3d(ax, graph, positions, start, goal, path, order, title, n):
    edge_segments = []
    seen = set()
    for state, neighbors in graph.items():
        for nb in neighbors:
            key = tuple(sorted((state, nb)))
            if key not in seen:
                seen.add(key)
                edge_segments.append((positions[state], positions[nb]))
    ax.add_collection3d(Line3DCollection(edge_segments, colors="0.82", linewidths=0.7))

    visited_set = set(order)
    xs_v, ys_v, zs_v, xs_u, ys_u, zs_u = [], [], [], [], [], []
    for state, (x, y, z) in positions.items():
        if state in visited_set:
            xs_v.append(x); ys_v.append(y); zs_v.append(z)
        else:
            xs_u.append(x); ys_u.append(y); zs_u.append(z)
    if xs_u:
        ax.scatter(xs_u, ys_u, zs_u, color="0.8", s=26, depthshade=False)
    if xs_v:
        ax.scatter(xs_v, ys_v, zs_v, color="#378ADD", s=32, depthshade=False)

    path_xyz = [positions[s] for s in path]
    if len(path_xyz) > 1:
        px, py, pz = zip(*path_xyz)
        ax.plot(px, py, pz, color="#D85A30", linewidth=3.5, solid_capstyle="round")

    sx, sy, sz = positions[start]
    gx, gy, gz = positions[goal]
    ax.scatter([sx], [sy], [sz], color="#1D9E75", s=160, depthshade=False,
               edgecolors="white", linewidths=1.2)
    ax.scatter([gx], [gy], [gz], color="#D85A30", s=160, depthshade=False,
               edgecolors="white", linewidths=1.2)

    ax.set_title(f"{title} \u2014 explored {len(order)} states, path length {len(path) - 1}",
                 fontsize=13, pad=14)
    ax.set_xticklabels([]); ax.set_yticklabels([]); ax.set_zticklabels([])
    ax.tick_params(axis='both', which='both', length=0, colors=(0, 0, 0, 0))
    ax.grid(False)
    for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
        pane.pane.set_visible(False)

    all_coords = list(positions.values())
    xs_all = [c[0] for c in all_coords]
    ys_all = [c[1] for c in all_coords]
    zs_all = [c[2] for c in all_coords]
    span = max(max(xs_all) - min(xs_all), max(ys_all) - min(ys_all), max(zs_all) - min(zs_all), 1.0)
    cx, cy, cz = sum(xs_all) / len(xs_all), sum(ys_all) / len(ys_all), sum(zs_all) / len(zs_all)
    pad = span * 0.15
    ax.set_xlim(cx - span / 2 - pad, cx + span / 2 + pad)
    ax.set_ylim(cy - span / 2 - pad, cy + span / 2 + pad)
    ax.set_zlim(cz - span / 2 - pad, cz + span / 2 + pad)
    ax.set_box_aspect((1, 1, 1))


# ---------------------------------------------------------------------------
# Tab 2: Scaling analysis
# ---------------------------------------------------------------------------

class ScalingTab(QWidget):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        self.worker = None

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Max dimension:"))
        self.max_dim_spin = QSpinBox()
        self.max_dim_spin.setRange(3, MAX_SCALING_DIM)
        self.max_dim_spin.setValue(10)
        controls.addWidget(self.max_dim_spin)
        self.run_btn = QPushButton("Run experiment")
        self.run_btn.clicked.connect(self.run_experiment)
        controls.addWidget(self.run_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.figure = Figure(figsize=(11, 4.5))
        self.canvas = FigureCanvas(self.figure)
        self.ax_explored, self.ax_path = self.figure.subplots(1, 2)
        layout.addWidget(self.canvas)

        self.table = QTableWidget()
        self.table.setMaximumHeight(180)
        layout.addWidget(self.table)

        self.run_experiment()

    def run_experiment(self):
        max_dim = self.max_dim_spin.value()
        self.run_btn.setEnabled(False)
        self.status_bar.showMessage(f"Running BFS / DFS / A* for n = 2..{max_dim}...")
        self.worker = ScalingWorker(max_dim)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_done(self, results):
        dims = [r["dimension"] for r in results]

        self.ax_explored.clear()
        for name in ALGORITHMS:
            self.ax_explored.plot(dims, [r[f"{name}_explored"] for r in results], marker='o', label=name)
        self.ax_explored.set_yscale("log")
        self.ax_explored.set_xlabel("dimension (n)")
        self.ax_explored.set_ylabel("states explored (log scale)")
        self.ax_explored.set_title("States explored vs dimension")
        self.ax_explored.legend()
        self.ax_explored.grid(alpha=0.3)

        self.ax_path.clear()
        for name in ALGORITHMS:
            self.ax_path.plot(dims, [r[f"{name}_path"] for r in results], marker='o', label=name)
        self.ax_path.set_xlabel("dimension (n)")
        self.ax_path.set_ylabel("path length found")
        self.ax_path.set_title("Path length vs dimension")
        self.ax_path.legend()
        self.ax_path.grid(alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw_idle()

        self.populate_table(results)
        self.run_btn.setEnabled(True)
        self.status_bar.showMessage("Done.", 3000)

    def populate_table(self, results):
        headers = ["n", "states", "BFS explored", "BFS path", "DFS explored", "DFS path",
                   "A* explored", "A* path"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            values = [r["dimension"], r["states"], r["BFS_explored"], r["BFS_path"],
                      r["DFS_explored"], r["DFS_path"], r["A*_explored"], r["A*_path"]]
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hypercube Search Explorer")
        self.resize(1200, 850)

        status = QStatusBar()
        self.setStatusBar(status)

        tabs = QTabWidget()
        tabs.addTab(GraphExplorerTab(status), "Graph explorer")
        tabs.addTab(ScalingTab(status), "Scaling analysis")
        self.setCentralWidget(tabs)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()