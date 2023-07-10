import random
import time
from docplex.mp.model import Model
from typing import List
from collections import defaultdict
from pyvis.network import Network
import networkx as nx

class Item:
    def __init__(self, value: int, weight: int):
        self.value = value
        self.weight = weight
        self.ratio = value / weight


# generate random vector of items
def random_vector(min_value, max_value, size):
    return [Item(random.randint(min_value, max_value), random.randint(min_value, max_value)) for _ in range(size)]


# do some test with increasing number of items
def do_some_tests():
    capacity = random.randint(6, 20)
    sizes = [10, 50, 100, 500, 1000]
    for num in sizes:
        items = random_vector(1, 30, num)
        items.sort(key=lambda x: x.ratio, reverse=True)

        fobj_bb, sel_bb, rc_bb, t_bb = solve_with_knapsack_cplex(items, capacity)
        fobj_pd, sel_pd, rc_pd, t_pd = solve_with_knapsack_dynamic(items, capacity)
        fobj_sp, sel_sp, rc_sp, t_sp = solve_with_shortest_path_dag(items, capacity, False)
        same = check_solution(sel_bb, sel_pd)
        same = check_solution(sel_bb, sel_sp) and same
        print(f'\nNumber of items: {num}')
        print(f'Capacity: {capacity}')
        print(f'FObj BB: {fobj_bb}, Time BB: {t_bb}')
        print(f'FObj PD: {fobj_pd}, Time PD: {t_pd}')
        print(f'FObj SP: {fobj_sp}, Time SP: {t_sp}')
        print(f'Same solution: {same}')


# print items
def print_solution(fobj, sel, rc, time):
    print(f'Profit = {fobj}, Residual capacity = {rc}')
    for i in range(len(sel)):
        if sel[i] == 1:
            print(f'x[{i}] = {sel[i]}')

    print(f'Time = {time}')


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


def solve_with_knapsack_dynamic(items: List[Item], capacity: int):
    t = time.time()
    fobj, sel, rc = knapsack_dynamic(items, capacity)
    t = time.time() - t

    return fobj, sel, rc, t


# check if the solutions are the same
def check_solution(sel1, sel2):
    same = True
    for idx in range(len(sel1)):
        if sel1[idx] != sel2[idx] and same:
            same = False

    return same


# from vector to networkx graph
def vector_to_nx(items: List[Item], capacity: int):
    g = nx.DiGraph(capacity=capacity, items=len(items))

    x_offset = 100
    y_offset = 40

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


if __name__ == '__main__':
    # generate random items
    items = random_vector(1, 10, 10)
    #items = [Item(40, 4), Item(15, 2), Item(20, 3), Item(10, 1)]
    # set max weight
    #capacity = 6
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

    print('\n\nDo some tests')
    do_some_tests()
    print('\n\n')
