##trying dry run code
levels = { 1: 0, 2: 1, 3: 1, 4: 2 }
S={1,2,3,4}

print(set(levels.values()))

for i in set(levels.values()):
    print(i) 

nbl = {}

# nbl[0] = [0,1]
# print(nbl)
# nbl[1]=[]
# nbl[1].append(2)
# print(nbl)


for lvl in set(levels.values()):
    nbl[lvl] = []
    for node in levels:
        if (levels[node] == lvl):
            nbl[lvl].append(node)

print(nbl)
print(nbl.items())

for level,nodes in nbl.items():
    print(nodes)