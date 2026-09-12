"""
Hypercube State-Space Search Visualizer
========================================

Visualizes BFS, DFS, and A* search over an n-dimensional hypercube graph
(states = bitstrings of length n, edges = single bit flips).

Usage:
    python hypercube_viz.py --dim 4                 # graph view for one dimension
    python hypercube_viz.py --dim 3 5 7              # graph view for several dimensions
    python hypercube_viz.py --scaling --max-dim 10   # how explored/path length scale with n
    python hypercube_viz.py --dim 4 --scaling        # do both

Output images are written to the --output-dir (default: current directory).
"""

import argparse
import math
import os
from collections import deque
from itertools import product

import heapq
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D


# ---------------------------------------------------------------------------
# Core graph + search (same logic as the original script, with the A* path
# reconstruction bug fixed and visit *order* tracked for visualization).
# ---------------------------------------------------------------------------

def generate_states(n):
    return [''.join(s) for s in product("01", repeat=n)]


def get_neighbors(state):
    bits = list(state)
    neighbors = []
    for i in range(len(bits)):
        new_bits = bits.copy()
        new_bits[i] = '1' if new_bits[i] == '0' else '0'
        neighbors.append(''.join(new_bits))
    return neighbors


def build_hypercube(n):
    return {state: get_neighbors(state) for state in generate_states(n)}


def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))


def _reconstruct(parent, goal):
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path


def bfs(graph, start, goal):
    queue = deque([start])
    visited = {start}
    order = [start]
    parent = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                order.append(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    return _reconstruct(parent, goal), order


def dfs(graph, start, goal):
    stack = [start]
    visited = {start}
    order = [start]
    parent = {start: None}

    while stack:
        current = stack.pop()
        if current == goal:
            break
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                order.append(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)

    return _reconstruct(parent, goal), order


def a_star(graph, start, goal):
    priority_queue = [(0, start)]
    visited = set()
    order = []
    parent = {start: None}
    g_cost = {start: 0}

    while priority_queue:
        _, current = heapq.heappop(priority_queue)
        if current in visited:
            continue
        visited.add(current)
        order.append(current)
        if current == goal:
            break
        for neighbor in graph[current]:
            new_g = g_cost[current] + 1
            if neighbor not in g_cost or new_g < g_cost[neighbor]:
                g_cost[neighbor] = new_g
                f = new_g + hamming_distance(neighbor, goal)
                parent[neighbor] = current
                heapq.heappush(priority_queue, (f, neighbor))

    return _reconstruct(parent, goal), order


ALGORITHMS = {"BFS": bfs, "DFS": dfs, "A*": a_star}


# ---------------------------------------------------------------------------
# Layout: project the n-dimensional hypercube to 2D via a set of basis
# vectors (one per bit), spread by the golden angle and shrinking in
# magnitude so higher-order dimensions don't dominate the picture.
# ---------------------------------------------------------------------------

def layout_positions(n):
    basis = []
    radius = 1.0
    for i in range(n):
        theta = math.radians(i * 137.5)
        basis.append((radius * math.cos(theta), radius * math.sin(theta)))
        radius *= 0.55

    positions = {}
    for state in generate_states(n):
        x = y = 0.0
        for i, bit in enumerate(state):
            if bit == '1':
                x += basis[i][0]
                y += basis[i][1]
        positions[state] = (x, y)
    return positions


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_single_algorithm(ax, graph, positions, start, goal, path, order, title):
    edge_segments = []
    seen = set()
    for state, neighbors in graph.items():
        for nb in neighbors:
            key = tuple(sorted((state, nb)))
            if key not in seen:
                seen.add(key)
                edge_segments.append((positions[state], positions[nb]))
    ax.add_collection(LineCollection(edge_segments, colors="0.85", linewidths=0.6, zorder=1))

    visited_set = set(order)
    xs_v, ys_v, xs_u, ys_u = [], [], [], []
    for state, (x, y) in positions.items():
        if state in visited_set:
            xs_v.append(x); ys_v.append(y)
        else:
            xs_u.append(x); ys_u.append(y)
    ax.scatter(xs_u, ys_u, color="0.8", s=16, zorder=2)
    sc = ax.scatter(xs_v, ys_v, color="#378ADD", s=20, zorder=2)

    path_xy = [positions[s] for s in path]
    if len(path_xy) > 1:
        px, py = zip(*path_xy)
        ax.plot(px, py, color="#D85A30", linewidth=2.5, zorder=3, solid_capstyle="round")

    sx, sy = positions[start]
    gx, gy = positions[goal]
    ax.scatter([sx], [sy], color="#1D9E75", s=90, zorder=4, edgecolors="white", linewidths=1)
    ax.scatter([gx], [gy], color="#D85A30", s=90, zorder=4, edgecolors="white", linewidths=1)

    ax.set_title(f"{title}\nexplored {len(order)} states, path length {len(path) - 1}", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return sc


def visualize_dimension(n, output_dir):
    graph = build_hypercube(n)
    start, goal = "0" * n, "1" * n
    positions = layout_positions(n)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    fig.suptitle(f"Search algorithms on the {n}-dimensional hypercube ({2 ** n} states)", fontsize=13)

    for ax, (name, algo) in zip(axes, ALGORITHMS.items()):
        path, order = algo(graph, start, goal)
        plot_single_algorithm(ax, graph, positions, start, goal, path, order, name)

    legend_elems = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#1D9E75', markersize=9, label='start'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#D85A30', markersize=9, label='goal'),
        Line2D([0], [0], color='#D85A30', linewidth=2.5, label='reconstructed path'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#378ADD', markersize=9, label='visited'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='0.8', markersize=9, label='unvisited'),
    ]
    fig.legend(handles=legend_elems, loc='lower center', ncol=4, fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))

    out_path = os.path.join(output_dir, f"hypercube_dim{n}.png")
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"saved {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Scaling experiment: explored states / path length vs dimension
# ---------------------------------------------------------------------------

def run_experiment(max_dimension):
    results = []
    for n in range(2, max_dimension + 1):
        graph = build_hypercube(n)
        start, goal = "0" * n, "1" * n
        row = {"dimension": n, "states": len(graph)}
        for name, algo in ALGORITHMS.items():
            path, order = algo(graph, start, goal)
            row[f"{name}_path"] = len(path) - 1
            row[f"{name}_explored"] = len(order)
        results.append(row)
    return results


def plot_scaling(results, output_dir):
    dims = [r["dimension"] for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for name in ALGORITHMS:
        axes[0].plot(dims, [r[f"{name}_explored"] for r in results], marker='o', label=name)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("dimension (n)")
    axes[0].set_ylabel("states explored (log scale)")
    axes[0].set_title("States explored vs dimension")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    for name in ALGORITHMS:
        axes[1].plot(dims, [r[f"{name}_path"] for r in results], marker='o', label=name)
    axes[1].set_xlabel("dimension (n)")
    axes[1].set_ylabel("path length found")
    axes[1].set_title("Path length vs dimension")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    out_path = os.path.join(output_dir, "hypercube_scaling.png")
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"saved {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Visualize hypercube search algorithms.")
    parser.add_argument("--dim", type=int, nargs="*", default=None,
                        help="One or more dimensions to draw as graphs (e.g. --dim 3 4 5).")
    parser.add_argument("--scaling", action="store_true",
                        help="Plot how explored states / path length scale with dimension.")
    parser.add_argument("--max-dim", type=int, default=10,
                        help="Max dimension for --scaling (default 10).")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Directory to save images to.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if not args.dim and not args.scaling:
        args.dim = [4]  # sensible default

    for n in (args.dim or []):
        visualize_dimension(n, args.output_dir)

    if args.scaling:
        results = run_experiment(args.max_dim)
        for r in results:
            print(r)
        plot_scaling(results, args.output_dir)


if __name__ == "__main__":
    main()