import ast
import operator
import networkx as nx
import matplotlib.pyplot as plt

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


# rule = "a == 2*b"
#rule = input("Enter relation rule: ")
rule = "a == b or a == 1"
#rule = "b==a+b"
#rule = "a==b-a"
print("Relation rule:", rule)

tree = ast.parse(rule, mode="eval")

print(ast.dump(tree, indent=2))

print(evaluate(tree.body, {"a" : 1, "b" : 2}))
print(evaluate(tree.body, {"a" : 5, "b" : 5}))
print(evaluate(tree.body, {"a" : 3, "b" : 6}))
print(evaluate(tree.body, {"a" : 8, "b" : 8}))