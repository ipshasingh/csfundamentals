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
for i in S:
    for j in S:
        x=(i,j)
        print("x:",x)
        CP.add(x)  
        if relation(str(i),str(j),op_use):   
            print("relation satisfied by:",x)   
            R.add(x)   

print("Cartesian Product:",CP)
print("Relation:",R)


