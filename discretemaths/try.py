import ast
import operator

def get_relation_rule():
    rule = input("Enter relation rule: ")
    return rule

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
rule = input("Enter relation rule: ")
#rule = "b==a+b"
#rule = "a==b-a"
print("Relation rule:", rule)

tree = ast.parse(rule, mode="eval")

print(ast.dump(tree, indent=2))

print(evaluate(tree.body, {"a" : 1, "b" : 2}))
print(evaluate(tree.body, {"a" : 10, "b" : 5}))
print(evaluate(tree.body, {"a" : 3, "b" : 6}))
print(evaluate(tree.body, {"a" : 1, "b" : 8}))

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

