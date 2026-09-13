import matplotlib.pyplot as plt
import networkx as nx
from logic import build_hypercube
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

graph = build_hypercube(4)

visualize_hypercube(graph)