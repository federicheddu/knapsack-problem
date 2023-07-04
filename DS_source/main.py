import random
import time
from docplex.mp.model import Model
from typing import List


class Item:
    def __init__(self, value: int, weight: int):
        self.value = value
        self.weight = weight
        self.ratio = value / weight


# generate random vector of items
def random_vector(min_value, max_value, size):
    return [Item(random.randint(min_value, max_value), random.randint(min_value, max_value)) for _ in range(size)]


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


if __name__ == '__main__':
    # generate random items
    items = random_vector(1, 10, 10)
    # sort items by ratio
    items.sort(key=lambda x: x.ratio, reverse=True)
    # set max weight
    capacity = 15

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

    print('\n\nDo some tests')
    do_some_tests()
