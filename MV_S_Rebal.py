import gurobipy as gp
from gurobipy import GRB, quicksum
import pandas as pd
import copy
import numpy as np

from MV_S_previous_data import fn
df = pd.read_excel('../Naive_S_P500.xlsx', sheet_name='return')
ret = copy.deepcopy(df.drop(columns=['Unnamed: 0']))
ret = ret.iloc[20:80, 1:397]

df = pd.read_excel('../Naive_S_P500.xlsx', sheet_name='price')
price = copy.deepcopy(df.drop(columns=['Unnamed: 0']))
price = price.iloc[0:1, 1:397]

n = [i for i in range(396)]
cov = ret.cov()
var = ret.var()
mean = ret.mean()
m = gp.Model('MVS_model')
m.params.NonConvex = 2

w_buy_b4_calc, w_minus_b4_calc = fn()
w_buy_cur = {}
w_minus_cur = {}

for i in range(396):
    w_buy_cur[i] = w_buy_b4_calc[i]*price.iloc[0, i]
    w_minus_cur[i] = w_minus_b4_calc[i]*price.iloc[0, i]

budget = sum(w_buy_cur) + sum(w_minus_cur)
w_buy_pre, w_minus_pre = {}, {}

for i in range(396):
    w_buy_pre[i] = w_buy_cur[i]/budget
    w_minus_pre[i] = w_minus_cur[i]/budget

# decision varibale
w_buy = {}
w_sold = {}
l_buy = {}
l_sold = {}
s_buy = {}
s_sold = {}
u = {}
v = {}
y = {}
for i in n:
    w_buy[i] = m.addVar(lb=0.0, ub=1.0, name="w_buy-%s" % i)
    w_sold[i] = m.addVar(lb=0.0, ub=1.0, name="w_sold-%s" % i)
    l_buy[i] = m.addVar(lb=0.0, ub=1.0, name="l_buy-%s" % i)
    l_sold[i] = m.addVar(lb=0.0, ub=1.0, name="l_sold-%s" % i)
    s_buy[i] = m.addVar(lb=0.0, ub=1.0, name="s_buy-%s" % i)
    s_sold[i] = m.addVar(lb=0.0, ub=1.0, name="s_sold-%s" % i)
    u[i] = m.addVar(lb=0.0, ub=1.0, vtype=GRB.BINARY, name="u-%s" % i)
    v[i] = m.addVar(lb=0.0, ub=1.0, vtype=GRB.BINARY, name="v-%s" % i)
    y[i] = m.addVar(lb=0.0, ub=1.0, vtype=GRB.BINARY, name="y-%s" % i)
m.update()

# coefficient
p1 = p2 = p3 = p4 = 0.001
k = 1

# objective
eq4 = quicksum(mean.iloc[i] * (w_buy[i] - w_sold[i]) for i in n)
eq5 = quicksum((w_buy[i] - w_sold[i])**2 * var.iloc[i] for i in n) + quicksum([cov.iloc[i, j] * (w_buy[i] - w_sold[i]) * (w_buy[j] - w_sold[j]) for i in n for j in n if i != j])
eq6 = quicksum(w_sold[i] for i in n)
eq7 = quicksum(p1*l_buy[i] + p2*l_sold[i] + p3*s_buy[i] + p4*s_sold[i] for i in n)

m.setObjective(eq4 - eq5 - eq6 - eq7, GRB.MAXIMIZE)

# constraints
eq8 = quicksum(w_buy[i] + k*w_sold[i] + p1*l_buy[i] + p2*l_sold[i] + p3*s_sold[i] + p4*s_sold[i] for i in n)
m.addConstr(eq8 == 1)
for i in n:
    m.addConstr(w_buy[i] == w_buy_pre[i] + l_buy[i] - l_sold[i])
    m.addConstr(w_sold[i] == w_minus_pre[i] + s_buy[i] - s_sold[i])
    m.addConstr(0.05*u[i] <= w_buy[i])
    m.addConstr(w_buy[i] <= 0.2*u[i])
    m.addConstr(0.05*v[i] <= w_sold[i])
    m.addConstr(w_sold[i] <= 0.2*v[i])
    m.addConstr(u[i] + v[i] == y[i])
m.optimize()
for v in m.getVars():
    if(v.X > 0 and ('w' in v.varName or 'l' in v.varName or 's' in v.varName)):
        print('%s %g' % (v.varName, v.x))
print('Obj: %g' % m.objVal)
