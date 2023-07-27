import random
import time
from docplex.mp.model import Model
from typing import List
from collections import defaultdict
from pyvis.network import Network
import networkx as nx
import os


## === ITEM DEFINITION AND GENERAL FUNCTIONS ================================================================================ ##

class Item:
    def __init__(self, value: int, weight: int):
        self.value = value
        self.weight = weight
        self.ratio = value / weight

# generate random vector of items
def random_items(min_value, max_value, size):
    return [Item(random.randint(min_value, max_value), random.randint(min_value, max_value)) for _ in range(size)]


# check if the solutions are the same
def check_solution(sel1, sel2):
    same = True
    for idx in range(len(sel1)):
        if sel1[idx] != sel2[idx] and same:
            same = False

    return same


# print items
def print_solution(fobj, sel, rc, time):
    print(f'Profit = {fobj}, Residual capacity = {rc}')
    for i in range(len(sel)):
        if sel[i] == 1:
            print(f'x[{i}] = {sel[i]}')
    print(f'Time = {time}')


## === BRANCH AND BOUND ===================================================================================================== ##

# solve knapsack problem using cplex
def knapsack_cplex(items: List[Item], capacity: int):
    # create model
    model = Model(name='knapsack')

    # create variables
    x = model.binary_var_list(len(items), name='x')

    # create objective function
    model.maximize(model.sum([items[i].value * x[i] for i in range(len(items))]))

    # create constraints
    model.add_constraint(model.sum([items[i].weight * x[i] for i in range(len(items))]) <= capacity)
    # set branch and bound strategy
    model.parameters.mip.strategy.branch.set(1)

    # solve model
    sol = model.solve()

    # return solution
    return sol, model


# solve knapsack problem using branch and bound of cplex
def solve_with_knapsack_cplex(items: List[Item], capacity: int):

    # solve knapsack problem using cplex
    t = time.time()
    sol, mdl = knapsack_cplex(items, capacity)
    t = time.time() - t

    # get parameters
    fobj = sol.objective_value
    sel = [v.solution_value for v in mdl.iter_binary_vars()]
    rc = capacity
    for i in range(len(items)):
        if sel[i] == 1:
            rc -= items[i].weight

    # cast to int
    fobj = int(fobj)
    sel = [int(x) for x in sel]

    return fobj, sel, rc, t


## === DYNAMIC PROGRAMMING ================================================================================================== ##

# solve knapsack problem using branch and bound
def knapsack_dynamic(items: List[Item], capacity: int):
    n = len(items)
    table = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    selected = [0] * n

    for i in range(n + 1):
        for j in range(capacity + 1):
            if i == 0 or j == 0:
                table[i][j] = 0
            elif items[i - 1].weight <= j:
                table[i][j] = max(items[i - 1].value + table[i - 1][j - items[i - 1].weight], table[i - 1][j])
            else:
                table[i][j] = table[i - 1][j]

    # Determine the selected items
    i = n
    j = capacity
    while i > 0 and j > 0:
        if table[i][j] != table[i - 1][j]:
            selected[i - 1] = 1
            j -= items[i - 1].weight
        i -= 1

    return table[n][capacity], selected, j

# solver
def solve_with_knapsack_dynamic(items: List[Item], capacity: int):
    t = time.time()
    fobj, sel, rc = knapsack_dynamic(items, capacity)
    t = time.time() - t

    return fobj, sel, rc, t


## === SHORTEST PATH ======================================================================================================== ##

# from vector to networkx graph
def vector_to_nx(items: List[Item], capacity: int, save_memory: bool = False):
    g = nx.DiGraph(capacity=capacity, items=len(items))

    x_offset = 100
    y_offset = 40

    if not save_memory:
        # add all nodes
        g.add_node(0, group=1, title=f'0', x=-x_offset/2, y=0)
        for layer in range(len(items)):
            for nd in range(1, capacity+2):
                g.add_node(layer*(capacity+1)+nd, group=layer+2, title=f'{layer*(capacity+1)+nd}', x=x_offset*(layer+1), y=y_offset*(nd-1))
        g.add_node(len(items)*(capacity+1)+1, group=len(items)+2, title=f'{len(items)*(capacity+1)+1}', x=x_offset*(len(items)+1.5), y=y_offset*capacity/2)

        # starting edges
        g.add_edge(0, 1, weight=0, title='0')
        if items[0].weight <= capacity:
            g.add_edge(0, items[0].weight+1, weight=-items[0].value, title=f'{items[0].value}')

        # edges between items
        # NOTE: layer*(capacity+1)+nd is the id of the item with the weight used in a graph
        for layer in range(len(items)-1):
            for nd in range(1, capacity+2):
                g.add_edge(layer*(capacity+1)+nd, (layer+1)*(capacity+1)+nd, weight=0, title='0')
                if nd-1 + items[layer+1].weight <= capacity:
                    g.add_edge(layer*(capacity+1)+nd, (layer+1)*(capacity+1)+nd+items[layer+1].weight, weight=-items[layer+1].value, title=f'{items[layer+1].value}')

        # ending edges
        for nd in range(1, capacity+2):
            g.add_edge((len(items)-1)*(capacity+1)+nd, len(items)*(capacity+1)+1, weight=0, title='0')

    else:

        queue = []
        target = len(items)*(capacity+1)+1
        
        # add source node
        g.add_node(0, group=1, title=f'0', x=-x_offset/2, y=0)
        # add target node
        g.add_node(len(items)*(capacity+1)+1, group=len(items)+2, title=f'{len(items)*(capacity+1)+1}', x=x_offset*(len(items)+1.5), y=y_offset*capacity/2)
        # add first nodes
        g.add_node(1, group=2, title=f'1', x=x_offset, y=y_offset)
        g.add_node(items[0].weight+1, group=2, title=f'{items[0].weight+1}', x=x_offset, y=y_offset*(items[0].weight))
        # add first edges
        g.add_edge(0, 1, weight=0, title='0')
        g.add_edge(0, items[0].weight+1, weight=-items[0].value, title=f'{items[0].value}')
        # add the nodes to the queue
        queue.append(1)
        queue.append(items[0].weight+1)


        # until the queue is empty => until we have added all the necessary nodes => until we created the nodes of the last item
        while queue:
            node = queue.pop(0)
            item = g.nodes[node]['group']-1

            # adding node and edge for the 'do not take' option
            new_node = node+capacity+1
            g.add_node(new_node, group=item+2, title=f'{new_node}', x=g.nodes[node]['x']+x_offset, y=g.nodes[node]['y'])
            g.add_edge(node, new_node, weight=0, title='0')
            # if the node is not already in the queue and it is not corresponding to the last item
            if new_node not in queue and item+1 < len(items)-1:
                queue.append(new_node)
            elif item+1 == len(items)-1:
                g.add_edge(new_node, target, weight=0, title='0')

            if (node-1) % (capacity+1) >= items[item+1].weight:
                new_node = node+capacity+1+items[item+1].weight
                g.add_node(new_node, group=g.nodes[node]['group']+1, title=f'{new_node}', x=g.nodes[node]['x']+x_offset, y=g.nodes[node]['y']+y_offset*items[item+1].weight)
                g.add_edge(node, new_node, weight=-items[item+1].value, title=f'{items[item+1].value}')
                # if the node is not already in the queue and it is not corresponding to the last item
                if new_node not in queue and item+1 < len(items)-1:
                    queue.append(new_node)
                elif item+1 == len(items)-1:
                    g.add_edge(new_node, target, weight=0, title='0')

    return g


# topological sort of a acyclic directed graph
def topological_sort(g, v, visited, stack):
    # mark the current node as visited
    visited[v] = True

    # recur for all adjacent vertices of v
    for i in g.neighbors(v):
        if visited[i] == False:
            topological_sort(g, i, visited, stack)

    stack.append(v)


# shortest path in a DAG
def shortest_path_dag(g: nx.DiGraph, s: int):
    visited = [False] * g.number_of_nodes()
    stack = []
    path = []
    sel = [0] * g.graph['items']

    for i in range(g.number_of_nodes()):
        if not visited[i]:
            topological_sort(g, s, visited, stack)

    dist = [float('inf')] * g.number_of_nodes()
    dist[s] = 0

    while stack:
        u = stack.pop()

        # update distance for all adjacent nodes
        for v in g.neighbors(u):
            if dist[v] > dist[u] + g[u][v]['weight']:
                dist[v] = dist[u] + g[u][v]['weight']

    idx = g.number_of_nodes()-1
    path.append(idx)
    for pred in g.predecessors(idx):
        if dist[pred] == dist[g.number_of_nodes()-1]:
            idx = pred
            path.append(idx)
            break
        
    #print(idx)
    while idx > 0:
        pred = list(g.predecessors(idx))
        #print(pred)
        if pred[0] == 0 or dist[idx] == dist[pred[0]] + g[pred[0]][idx]['weight']:
            idx = pred[0]
        else:
            idx = pred[1]
        #print(idx)
        path.append(idx)
    path.reverse()

    for nd in range(1,len(path)-1):
        if dist[path[nd]] != dist[path[nd-1]]:
            sel[g.nodes[path[nd]]['group']-2] = 1

    return dist, path, sel


# plot the graph using pyvis
def graph_plot(g: nx.DiGraph):
    gv = Network(width='100%', height='100%', notebook=False, directed=True, filter_menu=True)
    gv.toggle_physics(False)
    gv.from_nx(g)
    gv.show('graph.html')


# solve the knapsack problem using shortest (longest) path in a DAG
def solve_with_shortest_path_dag(items: List[Item], capacity: int, plot: bool = True):
    
    t = time.time()
    # create graph
    g = vector_to_nx(items, capacity)
    # solve shortest path problem
    fobj, path, sel = shortest_path_dag(g, 0)
    t = time.time() - t

    # calculate remaining capacity
    rc = capacity
    for i in range(len(items)):
        if sel[i] == 1:
            rc -= items[i].weight

    # plot the graph using pyvis
    if plot:
        graph_plot(g)

    return -fobj[len(fobj)-1], sel, rc, t


## === TESTS ================================================================================================================ ##

# do some test with increasing number of items
def do_some_tests():
    capacity = random.randint(6, 20)
    sizes = [10, 50, 100, 500, 1000]

    for num in sizes:
        items = random_items(1, 30, num)
        items.sort(key=lambda x: x.ratio, reverse=True)

        fobj_bb, sel_bb, rc_bb, t_bb = solve_with_knapsack_cplex(items, capacity)
        fobj_pd, sel_pd, rc_pd, t_pd = solve_with_knapsack_dynamic(items, capacity)
        fobj_sp, sel_sp, rc_sp, t_sp = solve_with_shortest_path_dag(items, capacity, False)
        same = check_solution(sel_bb, sel_pd)
        same = check_solution(sel_bb, sel_sp) and same

        print(f'\nNumber of items: {num}')
        print(f'Capacity: {capacity}')
        print(f'| Algorithm | Objective Function | Remaining Capacity | Time           |')
        print(f'| :-------: | :----------------: | :----------------: | :------------: |')
        print(f'| BB        | {fobj_bb}              | {rc_bb}                | {t_bb}   |')
        print(f'| PD        | {fobj_pd}              | {rc_pd}                | {t_pd}   |')
        print(f'| SP        | {fobj_sp}              | {rc_sp}                | {t_sp}   |')
        print(f'Same solution: {same}')


# solve the knapsack problem using all algorithms
def single_test(items: List[Item] = None, capacity: int = None):

    # if no items are given, generate random items
    if not items:
        items = random_items(1, 10, 10)
        capacity = random.randint(6, 15)

    print('\nList of items:')
    for it in range(len(items)):
        print(f'Itm[{it}]:\t value {items[it].value}\t weight {items[it].weight}')
    print(f'Capacity: {capacity}')

    print('\n========================================\n')

    print('\nBranch and Bound with CPLEX')
    fobj_bb, sel_bb, rc_bb, time_bb = solve_with_knapsack_cplex(items, capacity)
    print_solution(fobj_bb, sel_bb, rc_bb, time_bb)

    print('\n========================================\n')

    print('Dynamic Programming')
    fobj_pd, sel_pd, rc_pd, time_pd = solve_with_knapsack_dynamic(items, capacity)
    print_solution(fobj_pd, sel_pd, rc_pd, time_pd)

    print('\n========================================\n')

    # check if the solutions are the same
    same = check_solution(sel_bb, sel_pd)
    print(f'Branch and Bound with CPLEX and Dynamic Programming give the same solution: {same}')

    print('\n========================================\n')

    print('Shortest Path')
    fobj_sp, sel_sp, rc_sp, time_sp = solve_with_shortest_path_dag(items, capacity)
    print_solution(fobj_sp, sel_sp, rc_sp, time_sp)

    print('\n========================================\n')

    # check if the solutions are the same
    same = check_solution(sel_bb, sel_sp)
    print(f'Branch and Bound with CPLEX and Shortest Path give the same solution: {same} \n')

    print('\n========================================\n')


## === DATASET FUNCTIONS ==================================================================================================== ##

# read a dataset from a file
def read_dataset(file_name):
    # open file
    f = open(file_name, 'r')

    # read first line (num of items and capacity)
    line = f.readline()
    line = line.split()
    num_items = int(line[0])
    capacity = int(line[1])
    
    # read optimum
    line = f.readline()
    line = line.split()
    optimum = int(line[0])

    # read items
    items = []
    for line in f:
        line = line.split()
        items.append(Item(int(line[0]), int(line[1])))

    # close file
    f.close()

    return items, capacity, optimum


# read solution from a file
def read_solution(file_name):
    # open file
    f = open(file_name, 'r')

    # read array from first line
    line = f.readline()
    line = line.split()
    sel = [int(x) for x in line]

    return sel


# test a single dataset with all agorithms and print the results as markdown table
def single_dataset_test(dataset_file: str, solution_file: str):

    # read the dataset
    items, capacity, optimum = read_dataset(dataset_file)
    # read the solution
    sel = read_solution(solution_file)

    # solve the problem using all algorithms
    fobj_bb, sel_bb, rc_bb, t_bb = solve_with_knapsack_cplex(items, capacity)
    fobj_pd, sel_pd, rc_pd, t_pd = solve_with_knapsack_dynamic(items, capacity)
    fobj_sp, sel_sp, rc_sp, t_sp = solve_with_shortest_path_dag(items, capacity, False)

    same_bb = check_solution(sel, sel_bb)
    same_pd = check_solution(sel, sel_pd)
    same_sp = check_solution(sel, sel_sp)

    # print the solution as markdown table
    print(f'\n\nSolve the problem {dataset_file} with all algorithms - Optimum = {optimum}')
    print(f'| Algorithm | Objective Function | Remaining Capacity | Time           | Optimum selection |')
    print(f'| :-------: | :----------------: | :----------------: | :------------: | :-----: |')
    print(f'| BB        | {fobj_bb}              | {rc_bb}                | {t_bb}   | {same_bb} |')
    print(f'| PD        | {fobj_pd}              | {rc_pd}                | {t_pd}   | {same_pd} |')
    print(f'| SP        | {fobj_sp}              | {rc_sp}                | {t_sp}   | {same_sp} |')


# test all the knapsack problem dataset
def full_dataset_test():

    # sizes of the datasets
    sizes = [100, 200, 500, 1000, 2000, 5000, 10000]

    # test all datasets sizes
    for size in sizes:
        # for all the three datasets (uncorr, weakly and strongly corr)
        for idx in range(1, 4):
            # get the file name
            file_name = f'knapPI_{idx}_{size}_1000_1'
            dataset_file = f'./large_scale/{size}/{file_name}'
            solution_file = f'./large_scale-optimum/{size}/{file_name}'

            single_dataset_test(dataset_file, solution_file)

## === MAIN ================================================================================================================= ##

if __name__ == '__main__':

    # Tests to do
    single_test_fixed = False       # single test of knapsack problem with fixed problem
    single_test_random = False     # single test of knapsack problem with random problem
    single_test_dataset = False    # single test of knapsack problem from given dataset
    batch_test_random = False      # batch test of knapsack problem with random items and capacity
    dataset_test = True           # test with the knapsack problem dataset

    # solve the knapsack problem using all algorithms
    if single_test_fixed:
        print('\n\nSingle knapsack test:')
        items = [Item(40, 4), Item(15, 2), Item(20, 3), Item(10, 1)]
        capacity = 6
        single_test(items, capacity)
        print('\n\n')

    # solve a random knapsack problem using all algorithms
    if single_test_random:
        print('\n\nSingle knapsack test:')
        single_test()
        print('\n\n')

    # test with various sizes and random items
    if batch_test_random:
        print('\n\nRandom tests:')
        do_some_tests()
        print('\n\n')

    # solve a knapsack problem imported from file using all algorithms
    if single_test_dataset:
        print('\n\nDataset test:')
        single_dataset_test('large_scale/2000/knapPI_1_2000_1000_1', 'large_scale-optimum/2000/knapPI_1_2000_1000_1')
        print('\n\n')
        
    # do large scale tests
    if dataset_test:
        print('\n\Full dataset tests:')
        full_dataset_test()
