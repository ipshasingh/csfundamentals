from itertools import product
from collections import deque
import heapq
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx

def build_hypercube(n):
    states = generate_states(n)

    graph = {}

    for state in states:
        graph[state] = get_neighbors(state)

    return graph

def bfs(graph, start, goal):
    queue = deque([start])
    visited = {start}
    parent = {start: None}

    while queue:
        current = queue.popleft()

        if current == goal:
            break

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    # Reconstruct path
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path, visited

def bfs_with_events(graph, start, goal):
    queue = deque([start])
    visited = {start}
    parent = {start: None}

    events = []

    # Initial state
    events.append(("start", start))

    while queue:
        current = queue.popleft()

        # Current node being explored
        events.append(("current", current))

        if current == goal:
            events.append(("goal", current))
            break

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

                # Node has entered the frontier
                events.append(("frontier", neighbor))

        # Current node has finished exploration
        events.append(("explored", current))

    # Reconstruct path
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    # Animate final path
    events.append(("path", path))

    return path, visited, events

def animate_search(graph, start, goal, algorithm):

    G = nx.Graph()

    for state in graph:
        G.add_node(state)

    for state in graph:
        for neighbor in graph[state]:
            G.add_edge(state, neighbor)

    # Fixed layout so nodes don't move during animation
    pos = nx.spring_layout(G, seed=42)

    path, visited, events = get_search_events(
        graph,
        start,
        goal,
        algorithm
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    def draw(frame):

        ax.clear()

        event_type, data, *details = events[frame]

        # Default colour for every node
        node_colors = []

        for node in G.nodes:

            if node == start:
                node_colors.append("green")

            elif node == goal:
                node_colors.append("red")

            else:
                node_colors.append("lightblue")

        # Apply animation states
        for i, node in enumerate(G.nodes):

            # Look at everything that has happened so far
            for event in events[:frame + 1]:

                event_type, data = event

                if event_type == "frontier" and data == node:
                    node_colors[i] = "gold"

                elif event_type == "current" and data == node:
                    node_colors[i] = "orange"

                elif event_type == "explored" and data == node:
                    node_colors[i] = "yellow"

        # Draw graph
        nx.draw_networkx_edges(
            G,
            pos,
            ax=ax,
            edge_color="gray"
        )

        nx.draw_networkx_nodes(
            G,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=1200
        )

        nx.draw_networkx_labels(
            G,
            pos,
            ax=ax,
            font_size=10,
            font_weight="bold"
        )

        # Draw final path once path event occurs
        if event_type == "path":

            path_edges = list(zip(data[:-1], data[1:]))

            nx.draw_networkx_edges(
                G,
                pos,
                ax=ax,
                edgelist=path_edges,
                edge_color="orange",
                width=4
            )

        ax.set_title(
            f"{algorithm} Search\n"
            f"Step {frame + 1} / {len(events)}"
        )

        ax.axis("off")

    animation = FuncAnimation(
        fig,
        draw,
        frames=len(events),
        interval=500,
        repeat=False
    )

    plt.show()

def dfs(graph, start, goal):
    stack = [start]
    visited = {start}
    parent = {start: None}

    while stack:
        current = stack.pop()

        if current == goal:
            break

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)

    # Reconstruct path
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path, visited

def get_neighbors(state):
    bits = list(state)
    neighbors = []

    for i in range(len(bits)):
        new_bits = bits.copy()

        if new_bits[i] == '0':
            new_bits[i] = '1'
        else:
            new_bits[i] = '0'

        neighbors.append(''.join(new_bits))

    return neighbors


def generate_states(n):
    states = []

    for s in product("01", repeat=n):
        states.append(''.join(s))

    return states

def hamming_distance(state, goal):
    distance = 0

    for a, b in zip(state, goal):
        if a != b:
            distance += 1

    return distance

def dfs_with_events(graph, start, goal):
    stack = [start]
    visited = {start}
    parent = {start: None}

    events = []

    events.append(("start", start))

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

    # Reconstruct path
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    events.append(("path", path))

    return path, visited, events


def a_star(graph, start, goal):

    #A* prioritizes states with the smallest f 
    #f = g + h
    priority_queue = []
    heapq.heappush(priority_queue, (0, start))  #pushing in a priority heap
    #smalles f -> first out

    visited = set()  #tracking what we explore
    parent = {start: None} #remembering the path
    g_cost = {start: 0}  #visited path cost

    while priority_queue:
        _, current = heapq.heappop(priority_queue)  #removes state with smallest f

        if current in visited:
            continue
            #dont process a state twist

        visited.add(current)

        if current == goal:
            break

        for neighbor in graph[current]:
            #calculate cost to new neighbour
            new_g = g_cost[current] + 1

            if neighbor not in g_cost or new_g < g_cost[neighbor]:
                g_cost[neighbor] = new_g

                h = hamming_distance(neighbor, goal)
                #calculate the heuristic

                #calculate total estimated cost
                f = new_g + h

                parent[neighbor] = current
                heapq.heappush(priority_queue, (f, neighbor))

    # Reconstruct path
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path, visited

def a_star_with_events(graph, start, goal):
    priority_queue = []

    heapq.heappush(priority_queue, (0, start))

    visited = set()
    parent = {start: None}
    g_cost = {start: 0}

    events = []

    events.append(("start", start))

    while priority_queue:

        _, current = heapq.heappop(priority_queue)

        if current in visited:
            continue

        visited.add(current)

        h = hamming_distance(current, goal)
        f = g_cost[current] + h

        events.append((
            "current",
            current,
            g_cost[current],
            h,
            f
        ))

        if current == goal:
            events.append(("goal", current))
            break

        for neighbor in graph[current]:

            new_g = g_cost[current] + 1

            if neighbor not in g_cost or new_g < g_cost[neighbor]:

                g_cost[neighbor] = new_g

                h = hamming_distance(neighbor, goal)
                f = new_g + h

                parent[neighbor] = current

                heapq.heappush(
                    priority_queue,
                    (f, neighbor)
                )

                events.append((
                    "frontier",
                    neighbor,
                    new_g,
                    h,
                    f
                ))

        events.append(("explored", current))

    # Reconstruct path
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    events.append(("path", path))

    return path, visited, events

def visualize_hypercube(graph):
    G = nx.Graph()

    # Add states
    for state in graph:
        G.add_node(state)

    # Add edges
    for state in graph:
        for neighbor in graph[state]:
            G.add_edge(state, neighbor)

    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(10, 8))

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1200,
        font_size=10
    )

    plt.title("Hypercube State Space")
    plt.show()

def run_experiment(max_dimension):
    results = []

    for n in range(2, max_dimension + 1):
        graph = build_hypercube(n)

        start = "0" * n
        goal = "1" * n

        bfs_path, bfs_visited = bfs(graph, start, goal)
        dfs_path, dfs_visited = dfs(graph, start, goal)
        astar_path, astar_visited = a_star(graph, start, goal)

        results.append({
            "dimension": n,
            "states": len(graph),

            "bfs_path": len(bfs_path) - 1,
            "bfs_explored": len(bfs_visited),

            "dfs_path": len(dfs_path) - 1,
            "dfs_explored": len(dfs_visited),

            "astar_path": len(astar_path) - 1,
            "astar_explored": len(astar_visited)
        })

    return results

def get_search_events(graph, start, goal, algorithm):

    if algorithm == "BFS":
        return bfs_with_events(graph, start, goal)

    elif algorithm == "DFS":
        return dfs_with_events(graph, start, goal)

    elif algorithm == "A*":
        return a_star_with_events(graph, start, goal)

    else:
        raise ValueError("Unknown algorithm")

# print(generate_states(3))
# print(get_neighbors("000"))

# states = generate_states(2)

# graph = {}

# for state in states:
#     graph[state] = get_neighbors(state)

# print(graph)

# path, visited = bfs(graph, "00", "11")

# print("BFS")
# print("Path:", path)
# print("Visited:", visited)

# path, visited = dfs(graph, "00", "11")

# print("DFS")
# print("Path:", path)
# print("Visited:", visited)

# print("Hamming distance")
# print(hamming_distance("1010", "1111"))

# graph = build_hypercube(3)

# start = "000"
# goal = "111"

# bfs_path, bfs_visited = bfs(graph, start, goal)
# dfs_path, dfs_visited = dfs(graph, start, goal)
# astar_path, astar_visited = a_star(graph, start, goal)

# print("BFS:", bfs_path, len(bfs_visited))
# print("DFS:", dfs_path, len(dfs_visited))
# print("A*:", astar_path, len(astar_visited))

results = run_experiment(10)

for result in results:
    print(result)

graph = build_hypercube(4)

start = "0000"
goal = "1111"

animate_search(graph, start, goal, "DFS")