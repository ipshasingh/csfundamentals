from itertools import product
from collections import deque
import heapq

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
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path, visited

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