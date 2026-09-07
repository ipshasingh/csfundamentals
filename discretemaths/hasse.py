import ast
import operator 
import networkx as nx
import matplotlib.pyplot as plt

def show_op():
    op=['<','>','>=','==','!=']
    print(op)
    op_use=input("Enter the operater for relation: ")
    if op_use=="=":
        op_use = "=="
    return op_use

def enter_relation():
    rule = input("Enter relation rule:")
    return rule

def generate_tree(rule):
    tree= ast.parse(rule,mode="eval")
    print(ast.dump(tree,indent=2))
    return tree

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

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(evaluate(value, variables) for value in node.values)
        elif isinstance(node.op, ast.Or):
            return any(evaluate(value, variables) for value in node.values)
        else:
            raise ValueError("Unsupported comparison operator") 

def take_set():
    S=set()
    n=int(input("Enter the number of elements in the set: "))
    for i in range(n):
        x=int(input("Enter the element: "))
        S.add(x)
    return S

def relation(a,b,x):
    
    if eval(a+x+b):
        return True
    else:
        return False

def check_poset(S,R):
    if (reflexive(S,R) and antisymmetric(R) and transitive(R)):
        return True
    else:
        return False

def reflexive(S,R):
    for i in S:
        if (i,i) not in R:
            return False
    return True

def symmetric(R):
    for i in R:
        if (i[0],i[1]) in R and (i[1],i[0]) not in R:
            return False
    return True

def transitive(R):
    for i in R:
        for j in R:
            if i[1]==j[0] and (i[0],j[1]) not in R:
                return False
    return True

def antisymmetric(R):
    for i in R:
        for j in R:
            if i[0]==j[1] and i[1]==j[0] and i!=j:
                return False
    return True

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
    G.add_nodes_from(S)
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

def nodes_by_level(levels):
    nbl={}
    for lvl in set(levels.values()):
        nbl[lvl] = []
        for node in levels:
            if (levels[node] == lvl):
                nbl[lvl].append(node)
    return nbl

def assign_positions(nbl):
    pos = {}

    for level, nodes in nbl.items():
        count = len(nodes)

        for index, node in enumerate(nodes):
            x = index - (count - 1) / 2
            y = level

            pos[node] = (x, y)

    return pos

##creating graph 
def draw_hasse(S, immediate_rels, pos):
    G = nx.Graph()
    G.add_nodes_from(S)
    G.add_edges_from(immediate_rels)

    nx.draw(G, pos, with_labels=True)
    plt.show()
    

S=take_set()
print("Set is :",S)

CP=set()

# op_use=show_op()
# print("Relation def is : a",op_use,"b")


R=set()
rule = enter_relation()
tree = generate_tree(rule)
for i in S:
    for j in S:
        x=(i,j)
        # print("x:",x)
        CP.add(x)  
        if evaluate(tree.body, {"a" : i, "b" : j}):   
            #print("relation satisfied by:",x)   
            R.add(x)   

print("Cartesian Product:",CP)
print("Relation:",R)

isPoset=False
if check_poset(S,R):
    print("The relation is a poset")
    isPoset=True
else:
    print("The relation is not a poset")

immediate_rels = immediate_relationships(S,R)
print("Immediate relationships:", immediate_rels)

levels=assign_levels(S, immediate_rels)
print("Levels assigned to each element:", levels)

nbl = nodes_by_level(levels)
print("Nodes by level:", nbl)

pos = assign_positions(nbl)
print("Positions:", pos)

draw_hasse(S, immediate_rels, pos)


