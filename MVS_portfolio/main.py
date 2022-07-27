import pandas as pd
import copy
import MVS_function

df = pd.read_excel('../Naive_S_P500.xlsx', sheet_name='price')
price = copy.deepcopy(df.drop(columns=['Unnamed: 0'])).iloc[0:1, 1:397]
comp_name = list(price.columns)

budget_df = pd.DataFrame(columns=['Market Value'], )
w_plus_df, w_minus_df = pd.DataFrame(columns=list(comp_name), ), pd.DataFrame(columns=list(comp_name), )
w_df = pd.DataFrame(columns=list(comp_name), )
allocate_plus_df = pd.DataFrame(columns=list(comp_name), )
allocate_minus_df = pd.DataFrame(columns=list(comp_name), )
share_plus_df = pd.DataFrame(columns=list(comp_name), )
share_minus_df = pd.DataFrame(columns=list(comp_name), )

for i in range(158):
    if i == 0:
        budget_df.loc[len(budget_df.index)], w_plus_df.loc[len(w_plus_df.index)], w_minus_df.loc[len(w_minus_df.index)], \
        w_df.loc[len(w_df.index)], allocate_plus_df.loc[len(allocate_plus_df.index)], allocate_minus_df.loc[
            len(allocate_minus_df.index)], share_plus_df.loc[len(share_plus_df.index)], share_minus_df.loc[
            len(share_minus_df.index)] = MVS_function.get_first_optimization_data()
    else:
        budget_df.loc[len(budget_df.index)], w_plus_df.loc[len(w_plus_df.index)], w_minus_df.loc[len(w_minus_df.index)], \
        w_df.loc[len(w_df.index)], allocate_plus_df.loc[len(allocate_plus_df.index)], allocate_minus_df.loc[
            len(allocate_minus_df.index)], share_plus_df.loc[len(share_plus_df.index)], share_minus_df.loc[
            len(share_minus_df.index)] = MVS_function.get_others_optimization_date(i, list(share_plus_df.iloc[-1]),
                                                                                   list(share_minus_df.iloc[-1]))

with pd.ExcelWriter('../test.xlsx') as writer:
    budget_df.to_excel(writer, sheet_name='budget')
    w_plus_df.to_excel(writer, sheet_name='w_plus')
    w_minus_df.to_excel(writer, sheet_name='w_minus')
    w_df.to_excel(writer, sheet_name='w')
    allocate_plus_df.to_excel(writer, sheet_name='allocate_plus')
    allocate_minus_df.to_excel(writer, sheet_name='allocate_minus')
    share_plus_df.to_excel(writer, sheet_name='share_plus')
    share_minus_df.to_excel(writer, sheet_name='share_minus')
