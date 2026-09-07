import ast
import operator
import networkx as nx
import matplotlib.pyplot as plt

def get_relation_rule():
    rule = input("Enter relation rule: ")
    return rule

def draw_hasse(S,immediate_rels):
    G=nx.Graph() #not using digvraph cuz hasse diagram doesnt use arrows but positioning

    #adding elements as graph nodes
    G.add_nodes_from(S)

    #add cover relations as edges
    G.add_edges_from(immediate_rels)

def assign_levels(S, immediate_rels):
    # Create an empty directed graph.
    # We use a directed graph here because the cover relation has
    # a direction: a -> b means "b is above a" in the poset.
    G = nx.DiGraph()

    # Add all immediate/cover relationships as directed edges.
    # For example, {(1,2), (2,3)} creates:
    #
    #       1 -> 2 -> 3
    #
    G.add_edges_from(immediate_rels)

    # Create a dictionary to store the vertical level of every node.
    # Initially, we don't know the correct level, so every node starts at 0.
    #
    # Example:
    # S = {1, 2, 3, 4}
    # levels = {1: 0, 2: 0, 3: 0, 4: 0}
    levels = {node: 0 for node in S}

    # Process the nodes in topological order.
    # A topological ordering places every node before its successors.
    #
    # For example:
    #     1 -> 2 -> 3 -> 4
    #
    # gives:
    #     1, 2, 3, 4
    for node in nx.topological_sort(G):

        # Find all nodes that are directly above the current node.
        #
        # If we have:
        #     1 -> 2
        #
        # then G.successors(1) gives us 2.
        for successor in G.successors(node):

            # The successor must be at least one level above
            # the current node.
            #
            # So if:
            #     level[1] = 0
            #
            # then:
            #     level[2] >= 1
            #
            # max() is used because a node can have multiple
            # predecessors, and we want the highest level required
            # by any of them.
            levels[successor] = max(
                levels[successor],
                levels[node] + 1
            )

    # Return the completed dictionary containing the level
    # assigned to every element.
    return levels

def nodes_by_level(S,levels):
    node_level= {}
    for node in S:
        node_level[node]=  node_level.append()


def evaluate(node, variables):
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        return variables[node.id]

    if isinstance(node, ast.BinOp):
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

    if isinstance(node, ast.Compare):
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

    else:
        raise ValueError("Unsupported comparison operator") 

# rule = "a == 2*b"
#rule = input("Enter relation rule: ")
rule = "a==b"
#rule = "b==a+b"
#rule = "a==b-a"
print("Relation rule:", rule)

tree = ast.parse(rule, mode="eval")

print(ast.dump(tree, indent=2))

print(evaluate(tree.body, {"a" : 1, "b" : 2}))
print(evaluate(tree.body, {"a" : 5, "b" : 5}))
print(evaluate(tree.body, {"a" : 3, "b" : 6}))
print(evaluate(tree.body, {"a" : 8, "b" : 8}))

# print(tree.body.left.id)
# print(tree.body.ops[0])
# print(tree.body.comparators[0].left.value)
# print(tree.body.comparators[0].op)
# print(tree.body.comparators[0].right.id)
# print(type(tree.body.comparators[0].op).__name__)

# print(type(tree.body.ops[0]).__name__)
# print(type(tree.body.comparators[0].left).__name__)
# print(type(tree.body.comparators[0].right).__name__)

# print(eval("b == 2*a", {}, {"a": 2, "b": 4}))

def immediate_relationships(S,R):
    i_rels = set()
    
    for i in R:
        #i is a,b
        immediate = True
        a=i[0]
        b=i[1]
        if a==b:
            continue
        if a!=b:
            for c in S:
                if ((a,c) in R and (c,b) in R and (c!=a and c!=b)):                    
                    immediate = False
                    break
        if immediate:
            i_rels.add(i)
    return i_rels