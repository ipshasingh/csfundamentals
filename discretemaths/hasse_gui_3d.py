import ast
import sys

import networkx as nx
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# ============================================================
#                    POS​​ET / MATH ENGINE
# ============================================================

def parse_set(text):
    """
    Convert comma-separated input into a Python set.

    Example:
        "1, 2, 3, 4"
        -> {1, 2, 3, 4}
    """

    elements = set()

    for raw in text.split(","):
        raw = raw.strip()

        if not raw:
            continue

        try:
            elements.add(int(raw))
        except ValueError:
            elements.add(raw)

    return elements


def generate_tree(rule):
    """Parse the user's relation rule into an AST."""
    return ast.parse(rule, mode="eval")


def evaluate(node, variables):

    # --------------------------------------------------------
    # Constants
    # --------------------------------------------------------

    if isinstance(node, ast.Constant):
        return node.value


    # --------------------------------------------------------
    # Variables: a and b
    # --------------------------------------------------------

    elif isinstance(node, ast.Name):

        if node.id not in variables:
            raise ValueError(
                f"Unknown variable '{node.id}'. "
                "Only 'a' and 'b' are allowed."
            )

        return variables[node.id]


    # --------------------------------------------------------
    # Unary operators: +a, -a
    # --------------------------------------------------------

    elif isinstance(node, ast.UnaryOp):

        operand = evaluate(node.operand, variables)

        if isinstance(node.op, ast.USub):
            return -operand

        elif isinstance(node.op, ast.UAdd):
            return +operand

        raise ValueError("Unsupported unary operator")


    # --------------------------------------------------------
    # Binary operators
    # +  -  *  /  //  %
    # --------------------------------------------------------

    elif isinstance(node, ast.BinOp):

        left = evaluate(node.left, variables)
        right = evaluate(node.right, variables)

        if isinstance(node.op, ast.Add):
            return left + right

        elif isinstance(node.op, ast.Sub):
            return left - right

        elif isinstance(node.op, ast.Mult):
            return left * right

        elif isinstance(node.op, ast.Div):
            return left / right

        elif isinstance(node.op, ast.FloorDiv):
            return left // right

        elif isinstance(node.op, ast.Mod):
            return left % right

        raise ValueError("Unsupported binary operator")


    # --------------------------------------------------------
    # Comparisons
    # ==  !=  <  <=  >  >=
    # --------------------------------------------------------

    elif isinstance(node, ast.Compare):

        left = evaluate(node.left, variables)
        right = evaluate(node.comparators[0], variables)

        if isinstance(node.ops[0], ast.Eq):
            return left == right

        elif isinstance(node.ops[0], ast.NotEq):
            return left != right

        elif isinstance(node.ops[0], ast.Lt):
            return left < right

        elif isinstance(node.ops[0], ast.LtE):
            return left <= right

        elif isinstance(node.ops[0], ast.Gt):
            return left > right

        elif isinstance(node.ops[0], ast.GtE):
            return left >= right

        raise ValueError("Unsupported comparison operator")


    # --------------------------------------------------------
    # Boolean operators
    # and / or
    # --------------------------------------------------------

    elif isinstance(node, ast.BoolOp):

        if isinstance(node.op, ast.And):

            return all(
                evaluate(value, variables)
                for value in node.values
            )

        elif isinstance(node.op, ast.Or):

            return any(
                evaluate(value, variables)
                for value in node.values
            )

        raise ValueError("Unsupported boolean operator")


    # --------------------------------------------------------
    # Anything else
    # --------------------------------------------------------

    else:
        raise ValueError(
            f"Unsupported expression: {ast.dump(node)}"
        )


def build_relation(S, rule):

    tree = generate_tree(rule)

    R = set()

    for a in S:
        for b in S:

            result = evaluate(
                tree.body,
                {"a": a, "b": b}
            )

            if result:
                R.add((a, b))

    return R


# ============================================================
#                    POSET PROPERTIES
# ============================================================

def reflexive(S, R):

    for element in S:

        if (element, element) not in R:
            return False

    return True


def antisymmetric(R):

    for a, b in R:

        if a != b and (b, a) in R:
            return False

    return True


def transitive(R):

    for a, b in R:

        for c, d in R:

            if b == c:

                if (a, d) not in R:
                    return False

    return True


def check_poset(S, R):

    return (
        reflexive(S, R)
        and antisymmetric(R)
        and transitive(R)
    )


# ============================================================
#                    HASSE DIAGRAM LOGIC
# ============================================================

def cartesian_product(S):

    return {
        (a, b)
        for a in S
        for b in S
    }


def immediate_relationships(S, R):

    immediate = set()

    for a, b in R:

        # Ignore reflexive relationships
        if a == b:
            continue

        is_immediate = True

        for c in S:

            if (
                (a, c) in R
                and
                (c, b) in R
                and
                c != a
                and
                c != b
            ):
                is_immediate = False
                break

        if is_immediate:
            immediate.add((a, b))

    return immediate


def assign_levels(S, immediate_rels):

    G = nx.DiGraph()

    # Make sure isolated elements are included
    G.add_nodes_from(S)

    # a -> b means b is above a
    G.add_edges_from(immediate_rels)

    levels = {
        node: 0
        for node in S
    }

    for node in nx.topological_sort(G):

        for successor in G.successors(node):

            levels[successor] = max(
                levels[successor],
                levels[node] + 1
            )

    return levels


def nodes_by_level(levels):

    nbl = {}

    for level in set(levels.values()):

        nbl[level] = [
            node
            for node in levels
            if levels[node] == level
        ]

    return nbl


def assign_positions(nbl):

    pos = {}

    for level, nodes in nbl.items():

        count = len(nodes)

        for index, node in enumerate(nodes):

            # Center nodes horizontally around x = 0
            x = index - (count - 1) / 2

            # Level determines vertical position
            y = level

            pos[node] = (x, y)

    return pos


# ============================================================
#                         GUI
# ============================================================

class HasseWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Poset → Hasse Diagram")
        self.resize(1200, 750)

        # ----------------------------------------------------
        # Central widget
        # ----------------------------------------------------

        central = QWidget()

        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)


        # ----------------------------------------------------
        # Splitter
        # ----------------------------------------------------

        splitter = QSplitter(Qt.Horizontal)

        root_layout.addWidget(splitter)


        # ====================================================
        # LEFT PANEL
        # ====================================================

        left_panel = QWidget()

        left_layout = QVBoxLayout(left_panel)

        left_layout.setAlignment(Qt.AlignTop)


        # ----------------------------------------------------
        # Input box
        # ----------------------------------------------------

        input_box = QGroupBox("Poset Definition")

        input_layout = QVBoxLayout(input_box)


        # Set

        set_label = QLabel("Set elements:")

        input_layout.addWidget(set_label)

        self.set_input = QLineEdit()

        self.set_input.setPlaceholderText(
            "Example: 1, 2, 3, 4, 6, 12"
        )

        self.set_input.setText(
            "1, 2, 3, 4, 6, 12"
        )

        input_layout.addWidget(self.set_input)


        # Relation

        relation_label = QLabel(
            "Relation rule (use a and b):"
        )

        input_layout.addWidget(relation_label)

        self.rule_input = QLineEdit()

        self.rule_input.setPlaceholderText(
            "Example: b % a == 0"
        )

        self.rule_input.setText(
            "b % a == 0"
        )

        input_layout.addWidget(self.rule_input)


        # Hint

        hint = QLabel(
            "Examples:\n"
            "  a <= b             standard order\n"
            "  b % a == 0         divisibility\n"
            "  a == b or a == 1   boolean rules"
        )

        hint.setStyleSheet(
            "color: #77727F; font-size: 11px;"
        )

        input_layout.addWidget(hint)


        # Button

        self.generate_btn = QPushButton(
            "Generate Hasse Diagram"
        )

        self.generate_btn.clicked.connect(
            self.on_generate
        )

        input_layout.addWidget(
            self.generate_btn
        )


        left_layout.addWidget(input_box)


        # ====================================================
        # POSET STATUS
        # ====================================================

        status_box = QGroupBox("Poset Check")

        status_layout = QVBoxLayout(status_box)

        self.status_label = QLabel(
            "Waiting for input..."
        )

        self.status_label.setWordWrap(True)

        self.status_label.setStyleSheet(
            "font-weight: bold;"
        )

        status_layout.addWidget(
            self.status_label
        )

        left_layout.addWidget(
            status_box
        )


        # ====================================================
        # DETAILS
        # ====================================================

        details_box = QGroupBox("Details")

        details_layout = QVBoxLayout(
            details_box
        )

        self.details_text = QTextEdit()

        self.details_text.setReadOnly(True)

        self.details_text.setStyleSheet(
            """
            QTextEdit {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
                background-color: #FFFFFF;
                border: 1px solid #DDD8E5;
                border-radius: 6px;
                padding: 6px;
            }
            """
        )

        details_layout.addWidget(
            self.details_text
        )

        left_layout.addWidget(
            details_box,
            stretch=1
        )


        splitter.addWidget(left_panel)


        # ====================================================
        # RIGHT PANEL — GRAPH
        # ====================================================

        right_panel = QWidget()

        right_layout = QVBoxLayout(
            right_panel
        )


        # Matplotlib figure

        self.figure = Figure(
            figsize=(6, 6),
            facecolor="#FAF9FC"
        )

        self.canvas = FigureCanvas(
            self.figure
        )

        self.toolbar = NavigationToolbar(
            self.canvas,
            right_panel
        )

        self.ax = self.figure.add_subplot(
            111,
            projection="3d"
        )

        self._style_empty_axes()


        right_layout.addWidget(
            self.toolbar
        )

        right_layout.addWidget(
            self.canvas,
            stretch=1
        )


        rotate_hint = QLabel(
            "Tip: click and drag the diagram to rotate it."
        )

        rotate_hint.setStyleSheet(
            "color: #77727F; font-size: 11px;"
        )

        right_layout.addWidget(
            rotate_hint
        )


        splitter.addWidget(
            right_panel
        )

        splitter.setSizes(
            [400, 800]
        )


    # ========================================================
    #                      GUI HELPERS
    # ========================================================

    def _style_empty_axes(self):

        self.ax.clear()

        self.ax.set_facecolor(
            "#FAF9FC"
        )

        self.figure.patch.set_facecolor(
            "#FAF9FC"
        )

        self.ax.set_axis_off()

        self.canvas.draw_idle()


    def _set_status(self, text, ok):

        if ok:

            self.status_label.setStyleSheet(
                """
                font-weight: bold;
                color: #6B9B76;
                """
            )

        else:

            self.status_label.setStyleSheet(
                """
                font-weight: bold;
                color: #C77B86;
                """
            )

        self.status_label.setText(text)


    def _show_error(self, message, lines):

        self._set_status(
            "✗ " + message,
            False
        )

        lines = list(lines)

        lines.append("")
        lines.append(
            f"ERROR: {message}"
        )

        self.details_text.setPlainText(
            "\n".join(lines)
        )

        self._style_empty_axes()


    # ========================================================
    #                    MAIN GUI ACTION
    # ========================================================

    def on_generate(self):

        lines = []


        # ----------------------------------------------------
        # 1. Parse set
        # ----------------------------------------------------

        try:

            S = parse_set(
                self.set_input.text()
            )

            if not S:
                raise ValueError(
                    "The set is empty."
                )

        except Exception as exc:

            self._show_error(
                f"Set error: {exc}",
                lines
            )

            return


        lines.append(
            f"SET (n = {len(S)}):"
        )

        lines.append(
            f"  {sorted(S, key=str)}"
        )

        lines.append("")


        # ----------------------------------------------------
        # 2. Cartesian product
        # ----------------------------------------------------

        CP = cartesian_product(S)

        lines.append(
            f"CARTESIAN PRODUCT S × S "
            f"({len(CP)} pairs):"
        )

        lines.append(
            f"  {sorted(CP, key=str)}"
        )

        lines.append("")


        # ----------------------------------------------------
        # 3. Build relation
        # ----------------------------------------------------

        rule = (
            self.rule_input
            .text()
            .strip()
        )

        if not rule:

            self._show_error(
                "Please enter a relation rule.",
                lines
            )

            return


        try:

            R = build_relation(
                S,
                rule
            )

        except ZeroDivisionError:

            self._show_error(
                "Rule error: division/modulo by zero.",
                lines
            )

            return

        except SyntaxError as exc:

            self._show_error(
                f"Rule error: invalid syntax — {exc.msg}",
                lines
            )

            return

        except KeyError as exc:

            self._show_error(
                f"Rule error: unknown variable {exc}. "
                "Only a and b are available.",
                lines
            )

            return

        except Exception as exc:

            self._show_error(
                f"Rule error: {type(exc).__name__}: {exc}",
                lines
            )

            return


        lines.append(
            f"RELATION R defined by '{rule}' "
            f"({len(R)} pairs):"
        )

        lines.append(
            f"  {sorted(R, key=str)}"
        )

        lines.append("")


        # ----------------------------------------------------
        # 4. Poset properties
        # ----------------------------------------------------

        refl = reflexive(
            S,
            R
        )

        antisym = antisymmetric(
            R
        )

        trans = transitive(
            R
        )


        lines.append(
            "POSET PROPERTIES:"
        )

        lines.append(
            f"  Reflexive      : "
            f"{'✓ yes' if refl else '✗ no'}"
        )

        lines.append(
            f"  Antisymmetric  : "
            f"{'✓ yes' if antisym else '✗ no'}"
        )

        lines.append(
            f"  Transitive     : "
            f"{'✓ yes' if trans else '✗ no'}"
        )

        lines.append("")


        # ----------------------------------------------------
        # Not a poset
        # ----------------------------------------------------

        if not (
            refl
            and antisym
            and trans
        ):

            reasons = []

            if not refl:
                reasons.append(
                    "not reflexive"
                )

            if not antisym:
                reasons.append(
                    "not antisymmetric"
                )

            if not trans:
                reasons.append(
                    "not transitive"
                )


            self._set_status(
                "✗ Not a poset ("
                + ", ".join(reasons)
                + ")",
                False
            )


            lines.append(
                "RESULT:"
            )

            lines.append(
                "✗ Not a poset."
            )

            lines.append(
                "A Hasse diagram requires a valid poset."
            )


            self.details_text.setPlainText(
                "\n".join(lines)
            )

            self._style_empty_axes()

            return


        # ----------------------------------------------------
        # Valid poset
        # ----------------------------------------------------

        self._set_status(
            "✓ Valid Poset",
            True
        )


        lines.append(
            "RESULT:"
        )

        lines.append(
            "✓ Valid Poset"
        )

        lines.append("")


        # ----------------------------------------------------
        # 5. Hasse diagram calculations
        # ----------------------------------------------------

        immediate_rels = (
            immediate_relationships(
                S,
                R
            )
        )


        levels = assign_levels(
            S,
            immediate_rels
        )


        nbl = nodes_by_level(
            levels
        )


        pos = assign_positions(
            nbl
        )


        lines.append(
            f"IMMEDIATE / COVER RELATIONS "
            f"({len(immediate_rels)} pairs):"
        )

        lines.append(
            f"  {sorted(immediate_rels, key=str)}"
        )

        lines.append("")


        lines.append(
            "LEVELS:"
        )

        lines.append(
            f"  {dict(sorted(levels.items(), key=lambda x: str(x[0])))}"
        )

        lines.append("")


        lines.append(
            "NODES BY LEVEL:"
        )

        lines.append(
            f"  {nbl}"
        )

        lines.append("")


        lines.append(
            "POSITIONS:"
        )

        lines.append(
            f"  {pos}"
        )


        self.details_text.setPlainText(
            "\n".join(lines)
        )


        # ----------------------------------------------------
        # 6. Draw
        # ----------------------------------------------------

        try:

            self.draw_hasse_3d(
                S,
                immediate_rels,
                pos,
                levels
            )

        except Exception as exc:

            self._show_error(
                f"Drawing error: "
                f"{type(exc).__name__}: {exc}",
                lines
            )


    # ========================================================
    #                 DRAW HASSE DIAGRAM
    # ========================================================

    def draw_hasse_3d(
        self,
        S,
        immediate_rels,
        pos,
        levels
    ):

        self.ax.clear()

        self.ax.set_facecolor(
            "#FAF9FC"
        )

        self.figure.patch.set_facecolor(
            "#FAF9FC"
        )


        max_level = (
            max(levels.values())
            if levels
            else 0
        )


        # ----------------------------------------------------
        # Give nodes a tiny depth offset.
        # This keeps the 3D effect while maintaining
        # the mathematical level structure.
        # ----------------------------------------------------

        def depth(node):

            return (
                (hash(str(node)) % 7) - 3
            ) * 0.25


        coords = {}


        for node in S:

            x, level = pos[node]

            y = depth(node)

            z = level

            coords[node] = (
                x,
                y,
                z
            )


        # ----------------------------------------------------
        # Pastel palette
        # ----------------------------------------------------

        pastel_colors = [
            "#E8DDF5",   # lavender
            "#DDEBF7",   # baby blue
            "#F8DDE5",   # pastel pink
            "#F9E8C8",   # pastel peach
            "#DDF2E1",   # pastel green
            "#E6E0F8",   # soft violet
        ]


        # ----------------------------------------------------
        # Edges
        # ----------------------------------------------------

        for a, b in immediate_rels:

            xa, ya, za = coords[a]

            xb, yb, zb = coords[b]


            self.ax.plot(
                [xa, xb],
                [ya, yb],
                [za, zb],

                color="#A99BC4",

                linewidth=2,

                alpha=0.85
            )


        # ----------------------------------------------------
        # Nodes
        # ----------------------------------------------------

        for node in S:

            x, y, z = coords[node]

            level = levels[node]

            node_color = pastel_colors[
                level % len(pastel_colors)
            ]


            self.ax.scatter(
                [x],
                [y],
                [z],

                s=750,

                color=node_color,

                edgecolors="#8E849F",

                linewidths=1.2,

                depthshade=False
            )


            # ------------------------------------------------
            # Node label
            # ------------------------------------------------

            # Keep the label attached to the 3D node so it rotates
            # naturally with the diagram.
            self.ax.text(
                x,
                y,
                z,
                str(node),
                color="#403B4A",
                fontsize=12,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=10,
                clip_on=False
            )


        # ----------------------------------------------------
        # Remove axes
        # ----------------------------------------------------

        self.ax.set_axis_off()


        # ----------------------------------------------------
        # Camera
        # ----------------------------------------------------

        self.ax.view_init(
            elev=22,
            azim=-60
        )


        self.ax.set_box_aspect(
            (
                1,
                1,
                max(
                    0.6,
                    max_level * 0.6
                )
            )
        )


        self.canvas.draw_idle()


# ============================================================
#                         MAIN
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )


    # --------------------------------------------------------
    # Global light theme
    # --------------------------------------------------------

    app.setStyleSheet(
        """
        QWidget {
            background-color: #FAF9FC;
            color: #4A4655;
            font-size: 13px;
        }

        QMainWindow {
            background-color: #FAF9FC;
        }

        QGroupBox {
            background-color: #FFFFFF;
            border: 1px solid #DDD8E5;
            border-radius: 10px;
            margin-top: 12px;
            padding: 12px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 5px;
        }

        QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #D8D1E2;
            border-radius: 7px;
            padding: 8px;
        }

        QLineEdit:focus {
            border: 1px solid #B6A7D4;
        }

        QPushButton {
            background-color: #DCCFF0;
            color: #4A4655;
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #CFC0E7;
        }

        QPushButton:pressed {
            background-color: #C1B0DC;
        }

        QTextEdit {
            background-color: #FFFFFF;
            color: #4A4655;
        }

        QSplitter::handle {
            background-color: #E8E2EE;
        }
        """
    )


    window = HasseWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()