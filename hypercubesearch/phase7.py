
import sys
import time
import heapq
import random
import statistics
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
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QSpinBox, QSizePolicy, QScrollArea
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

        self.visualize_btn.clicked.connect(self.show_visualize)
        self.experiments_btn.clicked.connect(self.show_experiments)
        self.about_btn.clicked.connect(self.show_about)

        for button in (self.visualize_btn, self.experiments_btn, self.about_btn):
            button.setFixedHeight(38)
            button.setMinimumWidth(110)

        self.visualize_btn.setStyleSheet(self.active_button_style())

        header.addWidget(self.visualize_btn)
        header.addWidget(self.experiments_btn)
        header.addWidget(self.about_btn)

        root.addLayout(header)

        # Main pages
        self.pages = QStackedWidget()

        self.visualize_page = QWidget()
        visualize_layout = QHBoxLayout(self.visualize_page)
        visualize_layout.setContentsMargins(0, 0, 0, 0)
        visualize_layout.setSpacing(12)

        self.controls = self.create_controls()
        self.canvas = self.create_canvas()
        self.stats = self.create_stats()

        visualize_layout.addWidget(self.controls, 1)
        visualize_layout.addWidget(self.canvas, 3)
        visualize_layout.addWidget(self.stats, 1)

        self.experiments_page = self.create_experiments_page()

        self.pages.addWidget(self.visualize_page)
        self.pages.addWidget(self.experiments_page)

        root.addWidget(self.pages, 1)

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
        self.dimension_value.setFixedWidth(52)
        self.dimension_value.setFixedHeight(34)
        self.dimension_value.setAlignment(Qt.AlignCenter)
        self.dimension_value.setStyleSheet("""
            QLineEdit {
                color: #17325f;
                background: white;
                border: 1px solid #cbd7e8;
                border-radius: 6px;
                padding: 4px;
                font-size: 14px;
                font-weight: 600;
            }
            QLineEdit:focus {
                border: 1px solid #4d88f5;
            }
        """)
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
        self.start_edit.setStyleSheet("""
            QLineEdit {
                color: #17325f;
                background: white;
                border: 1px solid #cbd7e8;
                border-radius: 6px;
                padding: 7px;
            }
        """)
        self.start_edit.editingFinished.connect(self.state_changed)
        layout.addWidget(self.start_edit)

        layout.addWidget(self.section_label("Goal State"))

        self.goal_edit = QLineEdit(self.goal)
        self.goal_edit.setMaxLength(6)
        self.goal_edit.setStyleSheet("""
            QLineEdit {
                color: #17325f;
                background: white;
                border: 1px solid #cbd7e8;
                border-radius: 6px;
                padding: 7px;
            }
        """)
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
    # TOP NAVIGATION
    # --------------------------------------------------------

    def show_visualize(self):
        self.visualize_btn.setStyleSheet(self.active_button_style())
        self.experiments_btn.setStyleSheet("")
        self.about_btn.setStyleSheet("")
        self.pages.setCurrentWidget(self.visualize_page)

    def show_experiments(self):
        self.visualize_btn.setStyleSheet("")
        self.experiments_btn.setStyleSheet(self.active_button_style())
        self.about_btn.setStyleSheet("")

        self.pages.setCurrentWidget(self.experiments_page)
        self.run_experiments()

    def show_about(self):
        self.visualize_btn.setStyleSheet("")
        self.experiments_btn.setStyleSheet("")
        self.about_btn.setStyleSheet(self.active_button_style())

        QMessageBox.information(
            self,
            "About Hypercube Search Visualizer",
            "Hypercube Search Visualizer\n\n"
            "An interactive exploration of search algorithms "
            "on n-dimensional hypercubes.\n\n"
            "Algorithms: BFS, DFS and A*\n"
            "Heuristic: Hamming distance"
        )

    # --------------------------------------------------------
    # EXPERIMENTS
    # --------------------------------------------------------

    def create_experiments_page(self):
        # Keep the entire Experiments dashboard scrollable so that the
        # controls, findings, charts, and results table remain accessible
        # on smaller screens.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("Experiments")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            "Run repeatable experiments and compare search behaviour."
        )
        subtitle.setStyleSheet("color: #52617a;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        top.addLayout(title_box)
        top.addStretch()

        self.experiment_run_button = QPushButton("▶  Run Experiment")
        self.experiment_run_button.setMinimumHeight(40)
        self.experiment_run_button.setStyleSheet(self.primary_button_style())
        self.experiment_run_button.clicked.connect(self.run_experiments)
        top.addWidget(self.experiment_run_button)

        layout.addLayout(top)

        # Experiment controls
        controls_card = self.card()
        controls = QHBoxLayout(controls_card)
        controls.setContentsMargins(16, 12, 16, 12)
        controls.setSpacing(10)

        controls.addWidget(self.section_label("Experiment"))

        self.experiment_type = QComboBox()
        self.experiment_type.addItems([
            "Algorithm Comparison",
            "Dimension Scaling"
        ])
        self.experiment_type.setMinimumWidth(190)
        self.experiment_type.setStyleSheet(self.experiment_input_style())
        self.experiment_type.currentIndexChanged.connect(
            self.experiment_mode_changed
        )
        controls.addWidget(self.experiment_type)

        controls.addSpacing(8)
        controls.addWidget(self.section_label("Dimensions"))
        controls.addWidget(QLabel("From"))

        self.experiment_min = QSpinBox()
        self.experiment_min.setRange(2, 10)
        self.experiment_min.setValue(2)
        self.experiment_min.setStyleSheet(self.experiment_input_style())
        controls.addWidget(self.experiment_min)

        controls.addWidget(QLabel("To"))

        self.experiment_max = QSpinBox()
        self.experiment_max.setRange(2, 12)
        self.experiment_max.setValue(10)

        self.experiment_max.setStyleSheet(self.experiment_input_style())
        controls.addWidget(self.experiment_max)

        controls.addWidget(QLabel("Trials"))

        self.experiment_trials = QSpinBox()
        self.experiment_trials.setRange(1, 100)
        self.experiment_trials.setValue(10)
        self.experiment_trials.setStyleSheet(self.experiment_input_style())
        controls.addWidget(self.experiment_trials)

        controls.addStretch()

        self.experiment_summary = QLabel("Ready to run")
        self.experiment_summary.setStyleSheet(
            "color: #52617a; font-weight: 600;"
        )
        controls.addWidget(self.experiment_summary)

        layout.addWidget(controls_card)

        # Findings
        findings_card = self.card()
        findings_layout = QVBoxLayout(findings_card)
        findings_layout.setContentsMargins(16, 10, 16, 10)

        findings_title = QLabel("Findings")
        findings_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        findings_layout.addWidget(findings_title)

        self.findings_label = QLabel(
            "Run an experiment to generate a summary of the results."
        )
        self.findings_label.setWordWrap(True)
        self.findings_label.setStyleSheet("color: #52617a;")
        findings_layout.addWidget(self.findings_label)

        layout.addWidget(findings_card)

        # Charts
        charts = QHBoxLayout()
        charts.setSpacing(12)

        (
            self.path_chart_card,
            self.path_ax,
            self.path_canvas
        ) = self.create_chart_card(
            "Path Length vs Dimension",
            "Path Length"
        )

        (
            self.explored_chart_card,
            self.explored_ax,
            self.explored_canvas
        ) = self.create_chart_card(
            "States Explored vs Dimension",
            "States Explored"
        )

        charts.addWidget(self.path_chart_card, 1)
        charts.addWidget(self.explored_chart_card, 1)

        layout.addLayout(charts, 2)

        # Results table
        table_card = self.card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(14, 12, 14, 12)

        table_title = QLabel("Results Table")
        table_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        table_layout.addWidget(table_title)

        self.results_table = QTableWidget()
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setStyleSheet(self.experiment_table_style())
        self.results_table.setMinimumHeight(260)
        self.results_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_table.setWordWrap(False)

        # Keep columns readable instead of squeezing every column into the
        # available width. The table can now scroll horizontally when needed.
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)

        table_layout.addWidget(self.results_table)
        layout.addWidget(table_card)

        # A little extra space at the bottom makes the last table rows
        # reachable without feeling cramped.
        layout.addSpacing(20)

        scroll.setWidget(page)
        self.configure_algorithm_comparison_table()
        return scroll

    def experiment_input_style(self):
        return """
            QSpinBox, QComboBox {
                color: #17325f;
                background: white;
                border: 1px solid #b9c8dd;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 26px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
            QComboBox QAbstractItemView {
                color: #17325f;
                background: white;
                selection-background-color: #dce9ff;
                selection-color: #17325f;
            }
        """

    def experiment_table_style(self):
        return """
            QTableWidget {
                color: #17325f;
                background: white;
                gridline-color: #dbe4f2;
                font-size: 12px;
            }
            QHeaderView::section {
                color: #17325f;
                background: #eef4fc;
                border: none;
                border-bottom: 1px solid #dbe4f2;
                padding: 6px;
                font-weight: 600;
            }
        """

    def configure_algorithm_comparison_table(self):
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Algorithm",
            "Avg Path",
            "Path Std Dev",
            "Avg Explored",
            "Explored Std Dev"
        ])

    def configure_dimension_scaling_table(self):
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "n", "States",
            "BFS Avg", "DFS Avg", "A* Avg",
            "BFS Path", "DFS Path", "A* Path"
        ])

    def experiment_mode_changed(self):
        if self.experiment_type.currentText() == "Algorithm Comparison":
            self.configure_algorithm_comparison_table()
            self.experiment_max.setEnabled(False)
        else:
            self.configure_dimension_scaling_table()
            self.experiment_max.setEnabled(True)

    def create_chart_card(self, title, ylabel, log_y=False):
        card = self.card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        label = QLabel(title)
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(label)

        figure = Figure(figsize=(6, 3.5), facecolor="white")
        ax = figure.add_subplot(111)
        ax.set_facecolor("white")
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Dimension (n)")
        ax.grid(True, alpha=0.22)

        if log_y:
            ax.set_yscale("log")

        canvas = FigureCanvas(figure)
        layout.addWidget(canvas, 1)

        return card, ax, canvas

    def random_state_pair(self, n, rng):
        start = ''.join(rng.choice("01") for _ in range(n))
        goal = ''.join(rng.choice("01") for _ in range(n))

        while goal == start:
            goal = ''.join(rng.choice("01") for _ in range(n))

        return start, goal

    def run_single_trial(self, graph, n, rng):
        start_state, goal_state = self.random_state_pair(n, rng)

        results = {}
        for algorithm in ("BFS", "DFS", "A*"):
            path, visited, _ = get_search_events(
                graph, start_state, goal_state, algorithm
            )
            results[algorithm] = {
                "path": len(path) - 1,
                "explored": len(visited)
            }

        return results

    def mean_or_zero(self, values):
        return statistics.mean(values) if values else 0.0

    def std_or_zero(self, values):
        return statistics.stdev(values) if len(values) > 1 else 0.0

    def run_experiments(self):
        minimum = self.experiment_min.value()
        maximum = self.experiment_max.value()
        trials = self.experiment_trials.value()

        if minimum > maximum:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "The starting dimension must be less than or equal to the ending dimension."
            )
            return

        self.experiment_run_button.setEnabled(False)
        self.experiment_summary.setText("Running...")
        self.findings_label.setText("Running trials and collecting statistics...")
        QApplication.processEvents()

        # Fixed seed makes experiments reproducible.
        rng = random.Random(42)
        mode = self.experiment_type.currentText()

        try:
            if mode == "Algorithm Comparison":
                rows, dimension = self.run_algorithm_comparison(
                    minimum, trials, rng
                )
                self.populate_comparison_table(rows)
                self.plot_algorithm_comparison(rows, dimension)
                self.update_comparison_findings(rows, dimension, trials)

            else:
                rows = self.run_dimension_scaling(
                    minimum, maximum, trials, rng
                )
                self.populate_scaling_table(rows)
                self.plot_experiment_results(rows)
                self.update_scaling_findings(rows, trials)

        finally:
            self.experiment_run_button.setEnabled(True)

    def run_algorithm_comparison(self, dimension, trials, rng):
        graph = build_hypercube(dimension)
        raw = {
            "BFS": {"path": [], "explored": []},
            "DFS": {"path": [], "explored": []},
            "A*": {"path": [], "explored": []}
        }

        for _ in range(trials):
            trial = self.run_single_trial(graph, dimension, rng)
            for algorithm in raw:
                raw[algorithm]["path"].append(trial[algorithm]["path"])
                raw[algorithm]["explored"].append(trial[algorithm]["explored"])

        rows = []
        for algorithm in ("BFS", "DFS", "A*"):
            rows.append({
                "algorithm": algorithm,
                "avg_path": self.mean_or_zero(raw[algorithm]["path"]),
                "path_std": self.std_or_zero(raw[algorithm]["path"]),
                "avg_explored": self.mean_or_zero(raw[algorithm]["explored"]),
                "explored_std": self.std_or_zero(raw[algorithm]["explored"])
            })

        return rows, dimension

    def run_dimension_scaling(self, minimum, maximum, trials, rng):
        rows = []

        for n in range(minimum, maximum + 1):
            graph = build_hypercube(n)
            raw = {
                "BFS": {"path": [], "explored": []},
                "DFS": {"path": [], "explored": []},
                "A*": {"path": [], "explored": []}
            }

            for _ in range(trials):
                trial = self.run_single_trial(graph, n, rng)
                for algorithm in raw:
                    raw[algorithm]["path"].append(trial[algorithm]["path"])
                    raw[algorithm]["explored"].append(trial[algorithm]["explored"])

            rows.append({
                "dimension": n,
                "states": len(graph),
                "bfs_path": self.mean_or_zero(raw["BFS"]["path"]),
                "dfs_path": self.mean_or_zero(raw["DFS"]["path"]),
                "astar_path": self.mean_or_zero(raw["A*"]["path"]),
                "bfs_explored": self.mean_or_zero(raw["BFS"]["explored"]),
                "dfs_explored": self.mean_or_zero(raw["DFS"]["explored"]),
                "astar_explored": self.mean_or_zero(raw["A*"]["explored"]),
            })

        return rows

    def populate_comparison_table(self, rows):
        self.configure_algorithm_comparison_table()
        self.results_table.setRowCount(len(rows))

        for r, result in enumerate(rows):
            values = [
                result["algorithm"],
                f'{result["avg_path"]:.2f}',
                f'{result["path_std"]:.2f}',
                f'{result["avg_explored"]:.2f}',
                f'{result["explored_std"]:.2f}'
            ]

            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(r, c, item)

    def populate_scaling_table(self, rows):
        self.configure_dimension_scaling_table()
        self.results_table.setRowCount(len(rows))

        for r, result in enumerate(rows):
            values = [
                result["dimension"],
                result["states"],
                f'{result["bfs_explored"]:.2f}',
                f'{result["dfs_explored"]:.2f}',
                f'{result["astar_explored"]:.2f}',
                f'{result["bfs_path"]:.2f}',
                f'{result["dfs_path"]:.2f}',
                f'{result["astar_path"]:.2f}'
            ]

            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(r, c, item)

    def plot_algorithm_comparison(self, rows, dimension):
        algorithms = [r["algorithm"] for r in rows]
        avg_path = [r["avg_path"] for r in rows]
        avg_explored = [r["avg_explored"] for r in rows]

        self.path_ax.clear()
        self.path_ax.bar(algorithms, avg_path)
        self.path_ax.set_title(f"Dimension {dimension}")
        self.path_ax.set_xlabel("Algorithm")
        self.path_ax.set_ylabel("Average Path Length")
        self.path_ax.grid(True, axis="y", alpha=0.22)

        self.explored_ax.clear()
        self.explored_ax.bar(algorithms, avg_explored)
        self.explored_ax.set_title(f"Dimension {dimension}")
        self.explored_ax.set_xlabel("Algorithm")
        self.explored_ax.set_ylabel("Average States Explored")
        self.explored_ax.grid(True, axis="y", alpha=0.22)

        self.path_canvas.figure.tight_layout()
        self.explored_canvas.figure.tight_layout()
        self.path_canvas.draw()
        self.explored_canvas.draw()


    def plot_experiment_results(self, rows):
        dimensions = [r["dimension"] for r in rows]

        self.path_ax.clear()
        self.path_ax.plot(
            dimensions, [r["bfs_path"] for r in rows],
            marker="o", label="BFS"
        )
        self.path_ax.plot(
            dimensions, [r["dfs_path"] for r in rows],
            marker="o", label="DFS"
        )
        self.path_ax.plot(
            dimensions, [r["astar_path"] for r in rows],
            marker="o", label="A*"
        )
        self.path_ax.set_xlabel("Dimension (n)")
        self.path_ax.set_ylabel("Average Path Length")
        self.path_ax.grid(True, alpha=0.22)
        self.path_ax.legend()
        self.path_ax.set_xticks(dimensions)

        self.explored_ax.clear()
        self.explored_ax.plot(
            dimensions, [r["bfs_explored"] for r in rows],
            marker="o", label="BFS"
        )
        self.explored_ax.plot(
            dimensions, [r["dfs_explored"] for r in rows],
            marker="o", label="DFS"
        )
        self.explored_ax.plot(
            dimensions, [r["astar_explored"] for r in rows],
            marker="o", label="A*"
        )
        self.explored_ax.set_xlabel("Dimension (n)")
        self.explored_ax.set_ylabel("Average States Explored")
        self.explored_ax.set_yscale("log")
        self.explored_ax.grid(True, alpha=0.22)
        self.explored_ax.legend()
        self.explored_ax.set_xticks(dimensions)

        self.path_canvas.figure.tight_layout()
        self.explored_canvas.figure.tight_layout()
        self.path_canvas.draw()
        self.explored_canvas.draw()

        largest = rows[-1]
        self.experiment_summary.setText(
            f"{len(rows)} dimensions • largest space: {largest['states']:,} states"
        )

    def update_comparison_findings(self, rows, dimension, trials):
        best = min(rows, key=lambda r: r["avg_explored"])
        shortest = min(rows, key=lambda r: r["avg_path"])

        text = (
            f"Across {trials} random start/goal trials at n={dimension}, "
            f"{best['algorithm']} explored the fewest states on average "
            f"({best['avg_explored']:.2f}). "
            f"{shortest['algorithm']} produced the shortest average path "
            f"({shortest['avg_path']:.2f}). "
            "Standard deviation shows how much the result varied between trials."
        )
        self.findings_label.setText(text)
        self.experiment_summary.setText(
            f"n = {dimension} • {trials} random trials"
        )

    def update_scaling_findings(self, rows, trials):
        largest = rows[-1]
        growth = largest["states"] / rows[0]["states"]

        text = (
            f"Across {trials} random trials per dimension, the search space grew "
            f"from {rows[0]['states']:,} to {largest['states']:,} states "
            f"({growth:.0f}×). At n={largest['dimension']}, "
            f"average explored states were BFS {largest['bfs_explored']:.2f}, "
            f"DFS {largest['dfs_explored']:.2f}, and A* {largest['astar_explored']:.2f}."
        )
        self.findings_label.setText(text)

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
            value = int(self.dimension_value.text().strip())
        except ValueError:
            self.dimension_value.setText(str(self.dimension))
            return

        value = max(2, min(6, value))
        self.dimension_value.setText(str(value))
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
            color: #17325f;
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
