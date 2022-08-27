import gurobipy as gp
from gurobipy import GRB, quicksum
import pandas as pd
import copy

# df usage: df.iloc[:, 2:]
open_df = pd.read_excel('../result_1.xlsx', sheet_name='open').iloc[160:, :]
return7comp_df = pd.read_excel('../result_1.xlsx', sheet_name='return7comp')

comp_name = list(open_df.iloc[:, 2:].columns)

weight_df = pd.DataFrame(columns=comp_name)
weight_plus_df = pd.DataFrame(columns=comp_name)
weight_minus_df = pd.DataFrame(columns=comp_name)
e_plus_df = pd.DataFrame(columns=comp_name)
e_minus_df = pd.DataFrame(columns=comp_name)
weight_buying_df = pd.DataFrame(columns=comp_name)
weight_selling_df = pd.DataFrame(columns=comp_name)
weight_shortsell_df = pd.DataFrame(columns=comp_name)
weight_repurchasing_df = pd.DataFrame(columns=comp_name)

market_value_df = pd.DataFrame(columns=['Market value'])
allocate_plus_df = pd.DataFrame(columns=comp_name)
allocate_minus_df = pd.DataFrame(columns=comp_name)
shares_plus_df = pd.DataFrame(columns=comp_name)
shares_minus_df = pd.DataFrame(columns=comp_name)

# for t
for t in range(3):

# t = 0
    date = open_df.iloc[t].loc["Date"]
    ret7comp = return7comp_df.iloc[t, 2:]
    # o = open_df.iloc[20*t, 2:]

    n = [x for x in range(466)]
    m = gp.Model('momentum')
    m.params.NonConvex = 2


    # rebal
    if t == 0:
        budget = 1000000
        weight_plus_previous = [0 for x in range(466)]
        weight_minus_previous = [0 for x in range(466)]
    else:
        long_position = [x*y for x, y in zip(shares_plus_df.iloc[t - 1], open_df.iloc[20*t, 2:])]
        short_position = [x*y for x, y in zip(shares_minus_df.iloc[t - 1], open_df.iloc[20*t, 2:])]
        budget = sum(long_position) + sum(short_position)
        weight_plus_previous = [x / budget for x in long_position]
        weight_minus_previous = [x / budget for x in short_position]


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
    '''
    the different between first and others period is that the first period do not have previous weight plus and minus
    and the others period needs to consider the rebal each 20 days 
    '''
    m.addConstr(quicksum(
        weight_plus[i] + margin * weight_minus[i] + weight_buying[i] * ts1 + weight_selling[i] * ts2 + weight_shortsell[
            i] * ts3 + weight_repurchasing[i] * ts4 for i in n) == 1)
    for i in n:
        m.addConstr(weight_plus[i] + weight_minus[i] - e_plus[i] + e_minus[i] == 1 / 14)
        m.addConstr(weight_plus[i] == weight_plus_previous[i] + weight_buying[i] - weight_selling[i])
        m.addConstr(weight_minus[i] == weight_minus_previous[i] + weight_shortsell[i] - weight_repurchasing[i])
        m.addConstr(weight[i] == weight_plus[i] + weight_minus[i])

    for i in n:
        m.addConstr(low * buy_position[i] <= weight_plus[i])
        m.addConstr(weight_plus[i] <= up * buy_position[i])
        m.addConstr(low * shortsell_position[i] <= weight_minus[i])
        m.addConstr(weight_minus[i] <= up * shortsell_position[i])
        m.addConstr(buy_position[i] + shortsell_position[i] <= 1)
    m.setParam('OutputFlag', 0)
    m.optimize()
# get the result after optimize
# result write into dataframe
    e_plus_df.loc[t] = [v.x for k, v in e_plus.items()]
    e_minus_df.loc[t] = [v.x for k, v in e_minus.items()]
    weight_df.loc[t] = [v.x for k, v in weight.items()]
    weight_plus_df.loc[t] = [v.x for k, v in weight_plus.items()]
    weight_minus_df.loc[t] = [v.x for k, v in weight_minus.items()]
    weight_buying_df.loc[t] = [v.x for k, v in weight_buying.items()]
    weight_selling_df.loc[t] = [v.x for k, v in weight_selling.items()]
    weight_shortsell_df.loc[t] = [v.x for k, v in weight_shortsell.items()]
    weight_repurchasing_df.loc[t] = [v.x for k, v in weight_repurchasing.items()]

    market_value_df.loc[t] = [budget]
    allocate_plus_df.loc[t] = [budget * x for x in weight_plus_df.iloc[t]]
    allocate_minus_df.loc[t] = [budget * x for x in weight_minus_df.iloc[t]]
    shares_plus_df.loc[t] = [x/y for x, y in zip(allocate_plus_df.iloc[t], open_df.iloc[20*t, 2:])]
    shares_minus_df.loc[t] = [x/y for x, y in zip(allocate_minus_df.iloc[t], open_df.iloc[20*t, 2:])]

# market_value_df = pd.DataFrame(columns=['Market value'])
# allocate_plus_df = pd.DataFrame(columns=comp_name)
# allocate_minus_df = pd.DataFrame(columns=comp_name)
# shares_plus_df = pd.DataFrame(columns=comp_name)
# shares_minus_df = pd.DataFrame(columns=comp_name)



# df = pd.read_excel('../result_1.xlsx', sheet_name='return7comp')
# ret7comp = copy.deepcopy(df.iloc[0:1, 2:-3])
# comp_name = list(ret7comp.columns)
# w_p, w_m = [v.x for k, v in weight_plus.items()], [v.x for k, v in weight_minus.items()]
# w_plus_df, w_minus_df = pd.DataFrame(columns=list(comp_name), ), pd.DataFrame(columns=list(comp_name), )
#
# w_plus_df.loc[len(w_plus_df.index)] = w_p
# w_minus_df.loc[len(w_minus_df.index)] = w_m

with pd.ExcelWriter('0827.xlsx') as writer:
    weight_df.to_excel(writer, sheet_name='weight')
    weight_plus_df.to_excel(writer, sheet_name='weight_plus')
    weight_minus_df.to_excel(writer, sheet_name='weight_minus')
    e_plus_df.to_excel(writer, sheet_name='e_plus')
    e_minus_df.to_excel(writer, sheet_name='e_minus')
    weight_buying_df.to_excel(writer, sheet_name='weight_buying')
    weight_selling_df.to_excel(writer, sheet_name='weight_selling')
    weight_shortsell_df.to_excel(writer, sheet_name='weight_shortsell')
    weight_repurchasing_df.to_excel(writer, sheet_name='weight_repurchasing')

    market_value_df.to_excel(writer, sheet_name='market_value')
    allocate_plus_df.to_excel(writer, sheet_name='allocate_plus')
    allocate_minus_df.to_excel(writer, sheet_name='allocate_minus')
    shares_plus_df.to_excel(writer, sheet_name='shares_plus')
    shares_minus_df.to_excel(writer, sheet_name='shares_minus')

