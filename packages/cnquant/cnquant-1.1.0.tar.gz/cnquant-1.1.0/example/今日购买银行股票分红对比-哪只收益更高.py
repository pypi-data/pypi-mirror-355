import re

import pandas as pd

from cnquant import get_market_data_xq
from cnquant.core.name_symbol import name2symbol
from cnquant.data.dividend.dividend_ths import get_companies_dividend_ths
from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.update_data import update_symbols

initial_cash = 200000.0  # 现有资金
dividend_year = 2023  # 取用分红年份的数据


update_symbols()


# 监控的股票名称
names = [
    # 银行
    '中国银行',
    '农业银行',
    '工商银行',
    '建设银行',

    # 电信
    '中国移动',
    '中国电信',
    '中国联通',

    # 三桶油
    '中国石油',
    '中国石化',
    '中国海油',

    # 其他
    '贵州茅台',
    '中国平安',
    '美的集团',
]

symbols = [name2symbol(name) for name in names]  # 根据股票名称得到股票代码

# symbols = get_all_symbols()

# 获取现在的实时价格
price_df = get_market_data_xq(symbols)
price_df = price_df[['symbol', 'name', 'current', 'timestamp']]

# 获取上一年所有的分红金额，然后算出每股分红
dividend_df = get_companies_dividend_ths(symbols)
# 找到已经实施的方案
dividend_df = dividend_df[dividend_df['progress_name'] == '实施方案']
# 根据date取出分红的年份
dividend_df['year'] = dividend_df['date'].apply(lambda x: str(x)[:4])
# 取出需要年份的数据
dividend_df = dividend_df[dividend_df['year'] == str(dividend_year)]
# 取出需要的数据
dividend_df = dividend_df[['symbol', 'name', 'date', 'per_ten_pre_tax_dividend_ratio_rmb', 'year']]
dividend_df['per_ten_pre_tax_dividend_ratio_rmb'] = pd.to_numeric(dividend_df['per_ten_pre_tax_dividend_ratio_rmb'])  # 分红数据转为float
# 合并同一只股票同一年多次分红的数据
dividend_df_grouped = dividend_df.groupby(['symbol', 'year'], as_index=False).agg({
    'per_ten_pre_tax_dividend_ratio_rmb': 'sum',  # 累加同一股票同一年的分红
    'name': 'first'  # 选择任意一个值（假设每个 symbol 每年有唯一的公司名称）
})

# print(dividend_df_grouped)

# 合并价格跟分红数据
df = pd.merge(left=dividend_df_grouped, right=price_df, how='left', on=['symbol', 'name'])
# 计算目前价格购买分红率
df['dividend_rate'] = df['per_ten_pre_tax_dividend_ratio_rmb'] / (df['current'] * 10)
# 把股票名放到第二列
df.insert(1, 'name', df.pop('name'))

# 按分红率排名一下
df = df.sort_values(by='dividend_rate', ascending=False).reset_index(drop=True)

# 计算能买多少股票
df['can_buy_num'] = initial_cash / df['current']

# 计算一年能分红多少
df['1y_dividend'] = df['can_buy_num'] * df['per_ten_pre_tax_dividend_ratio_rmb'] / 10.0

# 然后输出dataframe，按分红金额从大到小排序
print(df)

# # 输出到桌面
# from pathlib import Path
# df.to_csv(Path.home() / r'Desktop\output.csv', encoding='utf-8-sig', index=False)



# df = pd.read_csv(r'C:\Users\dell\Desktop\output.csv')
#
# df = df[df['name'].str.contains('银行')]
# df.reset_index(drop=True, inplace=True)
# print(df)


