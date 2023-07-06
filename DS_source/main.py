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


# from vector to graph
def vector_to_nx(items: List[Item], capacity: int):
    g = nx.DiGraph()

    # add all nodes
    g.add_node(0, group=1, title=f'0')
    for layer in range(len(items)):
        for nd in range(1, capacity+2):
            g.add_node(layer*(capacity+1)+nd, group=layer+2, title=f'{layer*(capacity+1)+nd}')
    g.add_node(len(items)*(capacity+1)+1, group=len(items)+1, title=f'{len(items)*(capacity+1)+1}')

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


def do_some_tests():
    sizes = [10, 50, 100, 500, 1000]
    for num in sizes:
        items = random_vector(1, 30, num)
        items.sort(key=lambda x: x.ratio, reverse=True)
        capacity = 15

        fobj_bb, sel_bb, rc_bb, t_bb = solve_with_knapsack_cplex(items, capacity)
        fobj_pd, sel_pd, rc_pd, t_pd = solve_with_knapsack_dynamic(items, capacity)
        same = check_solution(sel_bb, sel_pd)
        print(f'\nNumber of items: {num} \n FObj BB: {fobj_bb}, Time BB: {t_bb} \n FObj PD: {fobj_pd}, Time PD: {t_pd} \n Same solution: {same}')


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


def topological_sort(g, v, visited, stack):
    # mark the current node as visited
    visited[v] = True

    # recur for all adjacent vertices of v
    for i in g.neighbors(v):
        if visited[i] == False:
            topological_sort(g, i, visited, stack)

    stack.append(v)


def shortest_path_dag(g: nx.DiGraph, s: int):
    visited = [False] * g.number_of_nodes()
    stack = []

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

    return dist


if __name__ == '__main__':
    # generate random items
    #items = random_vector(1, 10, 4)
    items = [Item(40, 4), Item(15, 2), Item(20, 3), Item(10, 1)]
    # sort items by ratio
    # items.sort(key=lambda x: x.ratio, reverse=True)
    # set max weight
    capacity = 6

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

    #print('\n\nDo some tests')
    #do_some_tests()

    g = vector_to_nx(items, capacity)
    fobj_sp = shortest_path_dag(g, 0)
    for idx in range(len(fobj_sp)):
        print(f'fobj[{idx}] = {fobj_sp[idx]}')


    gv = Network(width='100%', height='100%', notebook=False, directed=True, filter_menu=True)
    gv.toggle_physics(False)
    gv.from_nx(g)
    gv.show('graph.html')
