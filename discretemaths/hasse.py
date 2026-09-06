import ast
import operator 

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
        print("x:",x)
        CP.add(x)  
        if evaluate(tree.body, {"a" : i, "b" : j}):   
            print("relation satisfied by:",x)   
            R.add(x)   

print("Cartesian Product:",CP)
print("Relation:",R)


