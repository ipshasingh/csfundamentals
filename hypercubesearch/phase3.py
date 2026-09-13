
import sys
import time
import heapq
from itertools import product
from collections import deque

import networkx as nx
import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QSlider, QLineEdit,
    QRadioButton, QButtonGroup, QFrame, QProgressBar, QMessageBox,
    QSizePolicy
)


# ============================================================
# SEARCH / HYPERCUBE LOGIC
# ============================================================

def generate_states(n):
    return [''.join(s) for s in product("01", repeat=n)]


def get_neighbors(state):
    neighbors = []

    for i in range(len(state)):
        bits = list(state)
        bits[i] = '1' if bits[i] == '0' else '0'
        neighbors.append(''.join(bits))

    return neighbors


def build_hypercube(n):
    return {state: get_neighbors(state) for state in generate_states(n)}


def hamming_distance(state, goal):
    return sum(a != b for a, b in zip(state, goal))


def bfs_with_events(graph, start, goal):
    queue = deque([start])
    visited = {start}
    parent = {start: None}
    events = [("start", start)]

    while queue:
        current = queue.popleft()
        events.append(("current", current))

        if current == goal:
            events.append(("goal", current))
            break

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
                events.append(("frontier", neighbor))

        events.append(("explored", current))

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    events.append(("path", path))

    return path, visited, events


def dfs_with_events(graph, start, goal):
    stack = [start]
    visited = {start}
    parent = {start: None}
    events = [("start", start)]

    while stack:
        current = stack.pop()
        events.append(("current", current))

        if current == goal:
            events.append(("goal", current))
            break

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)
                events.append(("frontier", neighbor))

        events.append(("explored", current))

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    events.append(("path", path))

    return path, visited, events


def a_star_with_events(graph, start, goal):
    priority_queue = []
    heapq.heappush(priority_queue, (0, start))

    visited = set()
    parent = {start: None}
    g_cost = {start: 0}
    events = [("start", start)]

    while priority_queue:
        _, current = heapq.heappop(priority_queue)

        if current in visited:
            continue

        visited.add(current)

        g = g_cost[current]
        h = hamming_distance(current, goal)
        f = g + h

        events.append(("current", current, g, h, f))

        if current == goal:
            events.append(("goal", current))
            break

        for neighbor in graph[current]:
            new_g = g + 1

            if neighbor not in g_cost or new_g < g_cost[neighbor]:
                g_cost[neighbor] = new_g

                h = hamming_distance(neighbor, goal)
                f = new_g + h

                parent[neighbor] = current
                heapq.heappush(priority_queue, (f, neighbor))

                events.append(("frontier", neighbor, new_g, h, f))

        events.append(("explored", current))

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    events.append(("path", path))

    return path, visited, events


def get_search_events(graph, start, goal, algorithm):
    if algorithm == "BFS":
        return bfs_with_events(graph, start, goal)
    if algorithm == "DFS":
        return dfs_with_events(graph, start, goal)
    if algorithm == "A*":
        return a_star_with_events(graph, start, goal)

    raise ValueError("Unknown algorithm")


# ============================================================
# VISUALIZER
# ============================================================

class HypercubeVisualizer(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hypercube Search Visualizer")
        self.resize(1500, 900)

        self.dimension = 4
        self.start = "0000"
        self.goal = "1111"
        self.algorithm = "BFS"

        self.graph = {}
        self.G = nx.Graph()
        self.pos = {}

        self.path = []
        self.visited = set()
        self.events = []
        self.event_index = -1

        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.next_step)

        self.run_start_time = None
        self.elapsed = 0.0

        self.build_ui()
        self.reset_visualization()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("⬡  Hypercube Search Visualizer")
        title.setFont(QFont("Segoe UI", 21, QFont.Bold))

        subtitle = QLabel(
            "Explore how different search algorithms navigate an n-dimensional hypercube"
        )
        subtitle.setStyleSheet("color: #52617a; font-size: 13px;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.visualize_btn = QPushButton("Visualize")
        self.experiments_btn = QPushButton("Experiments")
        self.about_btn = QPushButton("About")

        for button in (self.visualize_btn, self.experiments_btn, self.about_btn):
            button.setFixedHeight(38)
            button.setMinimumWidth(110)

        self.visualize_btn.setStyleSheet(self.active_button_style())

        header.addWidget(self.visualize_btn)
        header.addWidget(self.experiments_btn)
        header.addWidget(self.about_btn)

        root.addLayout(header)

        # Main area
        main = QHBoxLayout()
        main.setSpacing(12)

        self.controls = self.create_controls()
        self.canvas = self.create_canvas()
        self.stats = self.create_stats()

        main.addWidget(self.controls, 1)
        main.addWidget(self.canvas, 3)
        main.addWidget(self.stats, 1)

        root.addLayout(main, 1)

    def create_controls(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        label = QLabel("Dimension (n)")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(label)

        dimension_row = QHBoxLayout()

        self.dimension_slider = QSlider(Qt.Horizontal)
        self.dimension_slider.setMinimum(2)
        self.dimension_slider.setMaximum(6)
        self.dimension_slider.setValue(self.dimension)
        self.dimension_slider.valueChanged.connect(self.dimension_changed)

        self.dimension_value = QLineEdit(str(self.dimension))
        self.dimension_value.setFixedWidth(48)
        self.dimension_value.setAlignment(Qt.AlignCenter)
        self.dimension_value.editingFinished.connect(self.dimension_text_changed)

        dimension_row.addWidget(self.dimension_slider)
        dimension_row.addWidget(self.dimension_value)

        layout.addLayout(dimension_row)

        ticks = QHBoxLayout()
        for i in range(2, 7):
            tick = QLabel(str(i))
            tick.setAlignment(Qt.AlignCenter)
            tick.setStyleSheet("color: #66758f; font-size: 11px;")
            ticks.addWidget(tick)
        layout.addLayout(ticks)

        layout.addSpacing(12)

        layout.addWidget(self.section_label("Start State"))

        self.start_edit = QLineEdit(self.start)
        self.start_edit.setMaxLength(6)
        self.start_edit.editingFinished.connect(self.state_changed)
        layout.addWidget(self.start_edit)

        layout.addWidget(self.section_label("Goal State"))

        self.goal_edit = QLineEdit(self.goal)
        self.goal_edit.setMaxLength(6)
        self.goal_edit.editingFinished.connect(self.state_changed)
        layout.addWidget(self.goal_edit)

        layout.addSpacing(8)

        layout.addWidget(self.section_label("Algorithm"))

        self.algorithm_group = QButtonGroup(self)

        for name in ("BFS", "DFS", "A*"):
            radio = QRadioButton({
                "BFS": "BFS (Breadth-First Search)",
                "DFS": "DFS (Depth-First Search)",
                "A*": "A* (A Star Search)"
            }[name])

            if name == "BFS":
                radio.setChecked(True)

            radio.toggled.connect(
                lambda checked, n=name: self.algorithm_selected(n, checked)
            )

            self.algorithm_group.addButton(radio)
            layout.addWidget(radio)

        layout.addSpacing(12)

        self.run_button = QPushButton("▶  Run Search")
        self.run_button.setMinimumHeight(46)
        self.run_button.clicked.connect(self.run_search)
        self.run_button.setStyleSheet(self.primary_button_style())
        layout.addWidget(self.run_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setMinimumHeight(42)
        self.reset_button.clicked.connect(self.reset_visualization)
        layout.addWidget(self.reset_button)

        layout.addStretch()

        return frame

    def create_canvas(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        self.graph_title = QLabel("Hypercube (n = 4)")
        self.graph_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.graph_title.setContentsMargins(8, 4, 0, 4)
        layout.addWidget(self.graph_title)

        self.figure = Figure(figsize=(8, 6), facecolor="white")
        self.ax = self.figure.add_subplot(111)

        self.canvas_widget = FigureCanvas(self.figure)
        self.canvas_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        layout.addWidget(self.canvas_widget, 1)

        legend = QLabel(
            "● Start     ● Goal     ● Unvisited     ● Frontier     "
            "● Current     ● Explored     ● Path"
        )
        legend.setStyleSheet("color: #53627b; font-size: 11px;")
        legend.setAlignment(Qt.AlignCenter)

        layout.addWidget(legend)

        return frame

    def create_stats(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        heading = QLabel("Search Statistics")
        heading.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(heading)

        self.stat_algorithm = self.stat_row(layout, "Algorithm")
        self.stat_dimension = self.stat_row(layout, "Dimension (n)")
        self.stat_states = self.stat_row(layout, "Total States")
        self.stat_explored = self.stat_row(layout, "States Explored")
        self.stat_path = self.stat_row(layout, "Path Length")
        self.stat_current = self.stat_row(layout, "Current State")
        self.stat_frontier = self.stat_row(layout, "Frontier Size")
        self.stat_time = self.stat_row(layout, "Time Elapsed")

        layout.addSpacing(12)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #d9e1ee;")
        layout.addWidget(line)

        heading2 = QLabel("Step Controls")
        heading2.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(heading2)

        buttons = QHBoxLayout()

        self.first_button = QPushButton("⏮")
        self.prev_button = QPushButton("◀")
        self.play_button = QPushButton("▶")
        self.next_button = QPushButton("▶")
        self.last_button = QPushButton("⏭")

        for button in (
            self.first_button,
            self.prev_button,
            self.play_button,
            self.next_button,
            self.last_button
        ):
            button.setMinimumHeight(38)

        self.first_button.clicked.connect(self.first_step)
        self.prev_button.clicked.connect(self.previous_step)
        self.play_button.clicked.connect(self.toggle_play)
        self.next_button.clicked.connect(self.next_step)
        self.last_button.clicked.connect(self.last_step)

        buttons.addWidget(self.first_button)
        buttons.addWidget(self.prev_button)
        buttons.addWidget(self.play_button)
        buttons.addWidget(self.next_button)
        buttons.addWidget(self.last_button)

        layout.addLayout(buttons)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.step_label = QLabel("Step: 0 / 0")
        self.step_label.setAlignment(Qt.AlignRight)
        self.step_label.setStyleSheet("color: #66758f;")
        layout.addWidget(self.step_label)

        layout.addStretch()

        return frame

    # --------------------------------------------------------
    # UI helpers
    # --------------------------------------------------------

    def card(self):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet("""
            QFrame#card {
                background: white;
                border: 1px solid #dbe4f2;
                border-radius: 10px;
            }
        """)
        return frame

    def section_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        return label

    def stat_row(self, layout, name):
        row = QHBoxLayout()

        left = QLabel(name)
        right = QLabel("0")

        left.setStyleSheet("color: #60708c; font-size: 12px;")
        right.setStyleSheet(
            "color: #17325f; font-size: 12px; font-weight: 600;"
        )

        row.addWidget(left)
        row.addStretch()
        row.addWidget(right)

        layout.addLayout(row)
        return right

    def active_button_style(self):
        return """
            QPushButton {
                background: #4d88f5;
                color: white;
                border-radius: 8px;
                padding: 7px 14px;
                font-weight: 600;
            }
        """

    def primary_button_style(self):
        return """
            QPushButton {
                background: #4d88f5;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #3978e9;
            }
        """

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    def dimension_changed(self, value):
        self.dimension = value
        self.dimension_value.setText(str(value))

        if self.start_edit.text() == self.start:
            self.start = "0" * value
            self.start_edit.setText(self.start)

        if self.goal_edit.text() == self.goal:
            self.goal = "1" * value
            self.goal_edit.setText(self.goal)

        self.reset_visualization()

    def dimension_text_changed(self):
        try:
            value = int(self.dimension_value.text())
        except ValueError:
            self.dimension_value.setText(str(self.dimension))
            return

        value = max(2, min(6, value))
        self.dimension_slider.setValue(value)

    def state_changed(self):
        start = self.start_edit.text().strip()
        goal = self.goal_edit.text().strip()

        if (
            len(start) != self.dimension
            or len(goal) != self.dimension
            or any(c not in "01" for c in start + goal)
        ):
            QMessageBox.warning(
                self,
                "Invalid State",
                f"Start and goal must be {self.dimension}-bit binary states."
            )
            self.start_edit.setText(self.start)
            self.goal_edit.setText(self.goal)
            return

        self.start = start
        self.goal = goal
        self.reset_visualization()

    def algorithm_selected(self, name, checked):
        if checked:
            self.algorithm = name
            self.reset_visualization()

    # --------------------------------------------------------
    # GRAPH
    # --------------------------------------------------------

    def build_graph(self):
        self.graph = build_hypercube(self.dimension)

        self.G = nx.Graph()

        for state in self.graph:
            self.G.add_node(state)

        for state in self.graph:
            for neighbor in self.graph[state]:
                self.G.add_edge(state, neighbor)

        # Deterministic layout for a stable animation.
        self.pos = nx.spring_layout(
            self.G,
            seed=42,
            k=1.8 / max(1, self.dimension - 1)
        )

    def draw_graph(self):
        self.ax.clear()
        self.ax.set_facecolor("white")

        if not self.G.nodes:
            self.canvas_widget.draw()
            return

        states_seen = set()
        frontier = set()
        current = None
        path_nodes = set()
        path_edges = []

        # Replay events up to current frame to derive visual state.
        for event in self.events[:self.event_index + 1]:
            kind = event[0]

            if kind == "frontier":
                frontier.add(event[1])
                states_seen.add(event[1])

            elif kind == "current":
                current = event[1]
                states_seen.add(event[1])

            elif kind == "explored":
                frontier.discard(event[1])
                states_seen.add(event[1])

            elif kind == "goal":
                current = event[1]

            elif kind == "path":
                self.path = event[1]
                path_nodes = set(self.path)
                path_edges = list(zip(self.path[:-1], self.path[1:]))

        # Edges first
        nx.draw_networkx_edges(
            self.G,
            self.pos,
            ax=self.ax,
            edge_color="#9aa8bd",
            width=1.2,
            alpha=0.9
        )

        # Base node groups
        unvisited = []
        explored = []
        frontier_nodes = []

        for node in self.G.nodes:
            if node == self.start or node == self.goal:
                continue

            if node in path_nodes:
                continue
            elif node == current:
                continue
            elif node in frontier:
                frontier_nodes.append(node)
            elif node in states_seen:
                explored.append(node)
            else:
                unvisited.append(node)

        if unvisited:
            nx.draw_networkx_nodes(
                self.G, self.pos, ax=self.ax,
                nodelist=unvisited,
                node_color="#cfe2ff",
                edgecolors="#6da3ff",
                node_size=850
            )

        if frontier_nodes:
            nx.draw_networkx_nodes(
                self.G, self.pos, ax=self.ax,
                nodelist=frontier_nodes,
                node_color="#ffd84d",
                edgecolors="#e6ad00",
                node_size=880
            )

        if explored:
            nx.draw_networkx_nodes(
                self.G, self.pos, ax=self.ax,
                nodelist=explored,
                node_color="#ffe58a",
                edgecolors="#e3bb38",
                node_size=850
            )

        if path_nodes:
            path_without_start_goal = [
                n for n in self.path
                if n != self.start and n != self.goal
            ]

            if path_without_start_goal:
                nx.draw_networkx_nodes(
                    self.G, self.pos, ax=self.ax,
                    nodelist=path_without_start_goal,
                    node_color="#ff9f43",
                    edgecolors="#e47b17",
                    node_size=900
                )

            if path_edges:
                nx.draw_networkx_edges(
                    self.G,
                    self.pos,
                    ax=self.ax,
                    edgelist=path_edges,
                    edge_color="#ff8c22",
                    width=4
                )

        if current is not None and current not in (self.start, self.goal):
            nx.draw_networkx_nodes(
                self.G, self.pos, ax=self.ax,
                nodelist=[current],
                node_color="#ff9f43",
                edgecolors="#d86f0b",
                node_size=930
            )

        # Start and goal always remain visually distinct.
        nx.draw_networkx_nodes(
            self.G, self.pos, ax=self.ax,
            nodelist=[self.start],
            node_color="#6bdc9b",
            edgecolors="#24aa68",
            node_size=950
        )

        if self.goal != self.start:
            nx.draw_networkx_nodes(
                self.G, self.pos, ax=self.ax,
                nodelist=[self.goal],
                node_color="#ff8b8b",
                edgecolors="#e55b5b",
                node_size=950
            )

        nx.draw_networkx_labels(
            self.G,
            self.pos,
            ax=self.ax,
            font_size=9 if self.dimension >= 5 else 10,
            font_weight="bold",
            font_color="#16325c"
        )

        self.ax.set_title(
            f"{self.algorithm} Search",
            fontsize=14,
            fontweight="bold",
            pad=12
        )

        self.ax.axis("off")
        self.figure.tight_layout()
        self.canvas_widget.draw()

    # --------------------------------------------------------
    # SEARCH / ANIMATION
    # --------------------------------------------------------

    def run_search(self):
        self.timer.stop()

        try:
            self.path, self.visited, self.events = get_search_events(
                self.graph,
                self.start,
                self.goal,
                self.algorithm
            )
        except Exception as exc:
            QMessageBox.critical(self, "Search Error", str(exc))
            return

        self.event_index = -1
        self.elapsed = 0.0
        self.run_start_time = time.perf_counter()

        self.progress.setRange(0, max(1, len(self.events) - 1))
        self.progress.setValue(0)

        self.run_button.setText("⏸  Pause")
        self.draw_graph()
        self.update_stats()

        self.timer.start()

    def toggle_play(self):
        if not self.events:
            self.run_search()
            return

        if self.timer.isActive():
            self.timer.stop()
            self.run_button.setText("▶  Resume")
            self.play_button.setText("▶")
        else:
            if self.event_index >= len(self.events) - 1:
                return

            self.timer.start()
            self.run_button.setText("⏸  Pause")
            self.play_button.setText("⏸")

    def next_step(self):
        if not self.events:
            return

        if self.event_index >= len(self.events) - 1:
            self.timer.stop()
            self.run_button.setText("▶  Run Search")
            self.play_button.setText("▶")
            return

        self.event_index += 1

        if self.run_start_time is not None:
            self.elapsed = time.perf_counter() - self.run_start_time

        self.progress.setValue(self.event_index)

        self.draw_graph()
        self.update_stats()

        if self.event_index >= len(self.events) - 1:
            self.timer.stop()
            self.run_button.setText("▶  Run Search")
            self.play_button.setText("▶")

    def previous_step(self):
        if not self.events:
            return

        self.timer.stop()
        self.event_index = max(-1, self.event_index - 1)

        self.progress.setValue(max(0, self.event_index))
        self.draw_graph()
        self.update_stats()

        self.run_button.setText("▶  Resume")

    def first_step(self):
        if not self.events:
            return

        self.timer.stop()
        self.event_index = -1
        self.progress.setValue(0)
        self.draw_graph()
        self.update_stats()

    def last_step(self):
        if not self.events:
            return

        self.timer.stop()
        self.event_index = len(self.events) - 1
        self.progress.setValue(self.event_index)
        self.draw_graph()
        self.update_stats()
        self.run_button.setText("▶  Run Search")

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    def update_stats(self):
        self.stat_algorithm.setText(self.algorithm)
        self.stat_dimension.setText(str(self.dimension))
        self.stat_states.setText(str(len(self.graph)))

        explored = set()
        frontier = set()
        current = "–"
        path_length = len(self.path) - 1 if self.path else 0

        g = h = f = None

        for event in self.events[:self.event_index + 1]:
            kind = event[0]

            if kind == "frontier":
                frontier.add(event[1])

                if len(event) >= 5:
                    g, h, f = event[2], event[3], event[4]

            elif kind == "current":
                current = event[1]
                frontier.discard(current)

                if len(event) >= 5:
                    g, h, f = event[2], event[3], event[4]

            elif kind == "explored":
                explored.add(event[1])
                frontier.discard(event[1])

            elif kind == "goal":
                current = event[1]

            elif kind == "path":
                path_length = len(event[1]) - 1

        self.stat_explored.setText(
            f"{len(explored)} ({(len(explored) / len(self.graph) * 100):.0f}%)"
            if self.graph else "0"
        )
        self.stat_path.setText(str(path_length))
        self.stat_current.setText(str(current))
        self.stat_frontier.setText(str(len(frontier)))
        self.stat_time.setText(f"{self.elapsed:.3f} s")

        # Show A* values in the current-state label when available.
        if self.algorithm == "A*" and current != "–" and g is not None:
            self.stat_current.setText(
                f"{current}   g={g} h={h} f={f}"
            )

        total = max(0, len(self.events) - 1)
        self.step_label.setText(
            f"Step: {max(0, self.event_index + 1)} / {total}"
        )

    def reset_visualization(self):
        self.timer.stop()

        self.run_button.setText("▶  Run Search")
        self.play_button.setText("▶")

        self.path = []
        self.visited = set()
        self.events = []
        self.event_index = -1
        self.run_start_time = None
        self.elapsed = 0.0

        self.graph_title.setText(f"Hypercube (n = {self.dimension})")

        self.build_graph()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

        self.update_stats()
        self.draw_graph()


# ============================================================
# APPLICATION
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            font-family: "Segoe UI";
            font-size: 12px;
        }

        QMainWindow {
            background: #f7f9fc;
        }

        QLineEdit {
            border: 1px solid #cbd7e8;
            border-radius: 6px;
            padding: 7px;
            background: white;
        }

        QLineEdit:focus {
            border: 1px solid #4d88f5;
        }

        QPushButton {
            border: 1px solid #d2ddec;
            border-radius: 7px;
            background: #f7f9fd;
            color: #263d65;
            padding: 6px 10px;
        }

        QPushButton:hover {
            background: #edf3fc;
        }

        QRadioButton {
            spacing: 7px;
            color: #4c6080;
            padding: 4px 0;
        }

        QSlider::groove:horizontal {
            height: 6px;
            background: #dce4ef;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
            background: #4d88f5;
        }

        QProgressBar {
            border: none;
            background: #e3e9f2;
            border-radius: 4px;
            height: 7px;
        }

        QProgressBar::chunk {
            background: #4d88f5;
            border-radius: 4px;
        }
    """)

    window = HypercubeVisualizer()
    window.show()

    sys.exit(app.exec())
