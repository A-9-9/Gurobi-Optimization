import gurobipy as gp
from gurobipy import GRB, quicksum
import pandas as pd
import copy

df = pd.read_excel('../result_1.xlsx', sheet_name='return7comp')
t = 0
ret7comp = copy.deepcopy(df.iloc[0:1, 2:-3]).iloc[0]

n = [x for x in range(466)]
m = gp.Model('momentum')
m.params.NonConvex = 2

# coefficient setting
buy_position = {x: 0 for x in n}
shortsell_position = {x: 0 for x in n}
ts1 = ts2 = ts3 = ts4 = 0.0025
up = 1
low = 0.0001
margin = 1

for i in n:
    if ret7comp[i] == 1:
        buy_position[i] = 1
    elif ret7comp[i] == -1:
        shortsell_position[i] = 1
    else:
        buy_position[i] = 0
        shortsell_position[i] = 0

# variable setting
e_plus = {}
e_minus = {}
weight = {}
weight_plus = {}
weight_minus = {}
weight_buying = {}
weight_selling = {}
weight_shortsell = {}
weight_repurchasing = {}

for i in n:
    e_plus[i] = m.addVar(lb=0.0, ub=1.0, name="entropy-plus-%s" % i)
    e_minus[i] = m.addVar(lb=0.0, ub=1.0, name="entropy-minus-%s" % i)
    weight[i] = m.addVar(lb=-1.0, ub=1.0, name="weight-%s" % i)
    weight_plus[i] = m.addVar(lb=0.0, ub=1.0, name="weight-plus-%s" % i)
    weight_minus[i] = m.addVar(lb=0.0, ub=1.0, name="weight-minus-%s" % i)
    weight_buying[i] = m.addVar(lb=0.0, ub=1.0, name="weight-buying-%s" % i)
    weight_selling[i] = m.addVar(lb=0.0, ub=1.0, name="weight-selling-%s" % i)
    weight_shortsell[i] = m.addVar(lb=0.0, ub=1.0, name="weight-shortsell-%s" % i)
    weight_repurchasing[i] = m.addVar(lb=0.0, ub=1.0, name="weight-repurchasing-%s" % i)
m.update()

# objective setting
entropy = quicksum(e_plus[i] + e_minus[i] for i in n)
m_obj = -entropy - quicksum(
    weight_buying[i] * ts1 + weight_selling[i] * ts2 + weight_shortsell[i] * ts3 + weight_repurchasing[i] * ts4 for i in
    n)
m.setObjective(m_obj, GRB.MAXIMIZE)

# constrain setting
m.addConstr(quicksum(
    weight_plus[i] + margin * weight_minus[i] + weight_buying[i] * ts1 + weight_selling[i] * ts2 + weight_shortsell[
        i] * ts3 + weight_repurchasing[i] * ts4 for i in n) == 1)
for i in n:
    m.addConstr(weight_plus[i] + weight_minus[i] - e_plus[i] + e_minus[i] == 1 / 14)
    m.addConstr(weight_plus[i] == weight_buying[i] - weight_selling[i])
    m.addConstr(weight_minus[i] == weight_shortsell[i] - weight_repurchasing[i])
    m.addConstr(weight[i] == weight_plus[i] + weight_minus[i])

for i in n:
    m.addConstr(low * buy_position[i] <= weight_plus[i])
    m.addConstr(weight_plus[i] <= up * buy_position[i])
    m.addConstr(low * shortsell_position[i] <= weight_minus[i])
    m.addConstr(weight_minus[i] <= up * shortsell_position[i])
    m.addConstr(buy_position[i] + shortsell_position[i] <= 1)

m.optimize()

df = pd.read_excel('../result_1.xlsx', sheet_name='return7comp')
ret7comp = copy.deepcopy(df.iloc[0:1, 2:-3])
comp_name = list(ret7comp.columns)
w_p, w_m = [v.x for k, v in weight_plus.items()], [v.x for k, v in weight_minus.items()]
w_plus_df, w_minus_df = pd.DataFrame(columns=list(comp_name), ), pd.DataFrame(columns=list(comp_name), )

w_plus_df.loc[len(w_plus_df.index)] = w_p
w_minus_df.loc[len(w_minus_df.index)] = w_m

with pd.ExcelWriter('0827.xlsx') as writer:
    w_plus_df.to_excel(writer, sheet_name='w_plus')
    w_minus_df.to_excel(writer, sheet_name='w_minus')

