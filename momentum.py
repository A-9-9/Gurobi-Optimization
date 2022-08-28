import gurobipy as gp
from gurobipy import GRB, quicksum
import pandas as pd
import copy

# data frame usage: df.iloc[:, 2:]

open_df = pd.read_excel('../result_1.xlsx', sheet_name='open').iloc[160:, :]
# return7comp_df = pd.read_excel('../result_1.xlsx', sheet_name='return7comp').iloc[:, :-3]
return10percent_df = pd.read_excel('../result_1.xlsx', sheet_name='return10percent').iloc[:, :]
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

market_value_df = pd.DataFrame(
    columns=['index', 'Date', 'Market value', 'out_obj', 'share+', 'share-', 'weight_ts', 'ts'])
allocate_plus_df = pd.DataFrame(columns=comp_name)
allocate_minus_df = pd.DataFrame(columns=comp_name)
shares_plus_df = pd.DataFrame(columns=comp_name)
shares_minus_df = pd.DataFrame(columns=comp_name)

# for
for t in range(93):
    date = open_df.iloc[20 * t].loc["Date"]

    # index = return7comp_df.iloc[t].loc["index"]
    index = return10percent_df.iloc[t].loc['index']
    # ret_comp = return7comp_df.iloc[t, 2:]
    ret_comp = return10percent_df.iloc[t, 2:]

    n = [x for x in range(466)]
    m = gp.Model('momentum')
    m.params.NonConvex = 2

    # rebal
    if t == 0:
        budget = 1000000
        weight_plus_previous = [0 for x in range(466)]
        weight_minus_previous = [0 for x in range(466)]
    else:
        long_position = [x * y for x, y in zip(shares_plus_df.iloc[t - 1], open_df.iloc[20 * t, 2:])]
        short_position = [x * y for x, y in zip(shares_minus_df.iloc[t - 1], open_df.iloc[20 * t, 2:])]
        budget = sum(long_position) + sum(short_position)
        weight_plus_previous = [x / budget for x in long_position]
        weight_minus_previous = [x / budget for x in short_position]

    # coefficient
    buy_position = {x: 0 for x in n}
    shortsell_position = {x: 0 for x in n}
    ts1 = ts2 = ts3 = ts4 = 0.0025
    up = 1
    low = 0.0001
    margin = 1

    for i in n:
        if ret_comp[i] == 1:
            buy_position[i] = 1
        elif ret_comp[i] == -1:
            shortsell_position[i] = 1
        else:
            buy_position[i] = 0
            shortsell_position[i] = 0

    # variable
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

    # objective
    entropy = quicksum(e_plus[i] + e_minus[i] for i in n)
    m_obj = -entropy - quicksum(
        weight_buying[i] * ts1 + weight_selling[i] * ts2 + weight_shortsell[i] * ts3 + weight_repurchasing[i] * ts4 for
        i in n)
    m.setObjective(m_obj, GRB.MAXIMIZE)

    '''
    constrain
    the different between first and others period is that 
    the first period do not have previous weight plus and minus, 
    and the others period needs to consider the rebal each 20 days 
    '''
    m.addConstr(quicksum(
        weight_plus[i] + margin * weight_minus[i] + weight_buying[i] * ts1 + weight_selling[i] * ts2 + weight_shortsell[
            i] * ts3 + weight_repurchasing[i] * ts4 for i in n) == 1)
    for i in n:
        # m.addConstr(weight_plus[i] + weight_minus[i] - e_plus[i] + e_minus[i] == 1 / 14)
        m.addConstr(weight_plus[i] + weight_minus[i] - e_plus[i] + e_minus[i] == 1 / (46 * 2))

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
    transaction_cost = quicksum(weight_buying[i] * ts1 + weight_selling[i] * ts2 + weight_shortsell[
        i] * ts3 + weight_repurchasing[i] * ts4 for i in n)

    m.optimize()

    # get the result after optimize
    # result write into dataframe
    ts_zip = zip([wb.x * ts1 for wb in weight_buying.values()], [v.x * ts2 for v in weight_selling.values()],
                 [v.x * ts3 for v in weight_shortsell.values()], [v.x * ts4 for v in weight_repurchasing.values()])
    obj = m.getObjective().getValue()
    share_plus = sum([1 for v in weight_plus.values() if v.x > 0])
    share_minus = sum([1 for v in weight_minus.values() if v.x > 0])
    weight_transaction_cost = sum([a + b + c + d for a, b, c, d in ts_zip])
    ts = budget * weight_transaction_cost
    result = [index, date, budget, obj, share_plus, share_minus, weight_transaction_cost, ts]

    e_plus_df.loc[t] = [v.x for k, v in e_plus.items()]
    e_minus_df.loc[t] = [v.x for k, v in e_minus.items()]
    weight_df.loc[t] = [v.x for k, v in weight.items()]
    weight_plus_df.loc[t] = [v.x for k, v in weight_plus.items()]
    weight_minus_df.loc[t] = [v.x for k, v in weight_minus.items()]
    weight_buying_df.loc[t] = [v.x for k, v in weight_buying.items()]
    weight_selling_df.loc[t] = [v.x for k, v in weight_selling.items()]
    weight_shortsell_df.loc[t] = [v.x for k, v in weight_shortsell.items()]
    weight_repurchasing_df.loc[t] = [v.x for k, v in weight_repurchasing.items()]

    market_value_df.loc[t] = result
    allocate_plus_df.loc[t] = [budget * x for x in weight_plus_df.iloc[t]]
    allocate_minus_df.loc[t] = [budget * x for x in weight_minus_df.iloc[t]]
    shares_plus_df.loc[t] = [x / y for x, y in zip(allocate_plus_df.iloc[t], open_df.iloc[20 * t, 2:])]
    shares_minus_df.loc[t] = [x / y for x, y in zip(allocate_minus_df.iloc[t], open_df.iloc[20 * t, 2:])]

with pd.ExcelWriter('0828_10percent.xlsx') as writer:
    weight_df.to_excel(writer, sheet_name='weight')
    weight_plus_df.to_excel(writer, sheet_name='weight_plus')
    weight_minus_df.to_excel(writer, sheet_name='weight_minus')
    e_plus_df.to_excel(writer, sheet_name='e_plus')
    e_minus_df.to_excel(writer, sheet_name='e_minus')
    weight_buying_df.to_excel(writer, sheet_name='weight_buying')
    weight_selling_df.to_excel(writer, sheet_name='weight_selling')
    weight_shortsell_df.to_excel(writer, sheet_name='weight_shortsell')
    weight_repurchasing_df.to_excel(writer, sheet_name='weight_repurchasing')

    market_value_df.to_excel(writer, sheet_name='result')
    allocate_plus_df.to_excel(writer, sheet_name='allocate_plus')
    allocate_minus_df.to_excel(writer, sheet_name='allocate_minus')
    shares_plus_df.to_excel(writer, sheet_name='shares_plus')
    shares_minus_df.to_excel(writer, sheet_name='shares_minus')

