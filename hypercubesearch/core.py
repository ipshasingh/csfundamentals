"""
Core logic for hypercube state-space search: graph construction, BFS/DFS/A*,
and a 2D layout for visualization. No GUI or plotting dependencies here.
"""

import heapq
import math
from collections import deque
from itertools import product


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


def layout_positions(n):
    """Project the n-dimensional hypercube to 2D: one basis vector per bit,
    spread by the golden angle, shrinking in magnitude per dimension."""
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


def layout_positions_3d(n, scale=200.0, decay=0.8):
    """Project the n-dimensional hypercube to 3D. The first three bits map
    to the standard x/y/z cube axes (so a 3-cube looks like a literal cube);
    any further bits get additional directions spread evenly over a sphere
    (Fibonacci sphere sampling), each shrinking by `decay` so higher-order
    dimensions read as nested, still-distinguishable sub-cubes."""
    vectors = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)][:n]

    extra = n - 3
    if extra > 0:
        radius = 1.0
        for i in range(extra):
            radius *= decay
            # Fibonacci sphere point for even angular spread
            phi = math.acos(1 - 2 * (i + 0.5) / extra)
            theta = math.pi * (1 + 5 ** 0.5) * i
            vectors.append((
                radius * math.sin(phi) * math.cos(theta),
                radius * math.sin(phi) * math.sin(theta),
                radius * math.cos(phi),
            ))

    positions = {}
    for state in generate_states(n):
        x = y = z = 0.0
        for i, bit in enumerate(state):
            if bit == '1':
                vx, vy, vz = vectors[i]
                x += vx * scale
                y += vy * scale
                z += vz * scale
        positions[state] = (x, y, z)
    return positions


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