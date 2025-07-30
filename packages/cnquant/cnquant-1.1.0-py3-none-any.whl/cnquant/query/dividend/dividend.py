import pandas as pd

from cnquant.config.config_data_path import get_file_path_dividend_ths
pd.set_option('max_colwidth', 200)
"""
# TODO: 每年分红金额排名
"""


def average_dividend_rate_rank(year_count=5):
    """
    计算最近几年的平均分红率排名
    :param year_count:
    :return:
    """
    df = _open_file()

    # 删除2023的数据，还没出来，分红率
    df = df[~(df['year_date'] == '2023')].reset_index(drop=True)

    # 分组计算每年的分红率，然后生成年份行
    gb_df = df.groupby(['symbol', 'year_date'])['pretax_dividend_rate'].sum().reset_index()
    # print(gb_df)

    # 筛选上市小于year_count年的公司
    grouped = gb_df.groupby('symbol')
    group_counts = grouped.size()
    # 筛选出数据量大于等于year_count-1的组
    large_groups = group_counts[group_counts > (year_count-1)].index
    # 从原始DataFrame中提取这些组的数据
    gb_df = gb_df[gb_df['symbol'].isin(large_groups)]

    # 取出最近5年的数据
    _gb_df = gb_df.groupby('symbol').apply(lambda x: x.iloc[-1 * year_count:])
    _gb_df.reset_index(inplace=True, drop=True)
    # print(_gb_df)

    # 计算平均值
    rate_df = _gb_df.groupby('symbol')['pretax_dividend_rate'].mean().reset_index()

    # 把名字添加进来
    _rate_df = pd.merge(left=rate_df, right=df[['symbol', 'name']], on='symbol', how='inner')
    _rate_df.drop_duplicates(inplace=True)

    # 排个名
    _rate_df.sort_values(by='pretax_dividend_rate', ascending=False, inplace=True)
    _rate_df.reset_index(inplace=True, drop=True)
    _rate_df['dividend_url'] = 'https://basic.10jqka.com.cn/astockpc/astockmain/index.html#/bonus?code=' + _rate_df['symbol']
    _rate_df['klinre_url'] = 'https://stockpage.10jqka.com.cn/' + _rate_df['symbol']

    print(f'{year_count}年平均分红率')
    print(_rate_df[:50])
    _rate_df.to_csv(f'~/Desktop/dividend_rate_{year_count}_year.csv', index=False, encoding='utf-8-sig')


def query_dividend_rate(year='2023'):
    df = _open_file()
    # df = df[df['year_date'] == year]
    df.reset_index(inplace=True, drop=True)

    # 把一年中分红率求和。保留：symbol, name, pretax_dividend_rate[求和后结果]，stock_dividend_total[求和后结果], update_date, year_date
    gb = df.groupby(['symbol', 'name', 'update_date', 'year_date']).agg({
        'pretax_dividend_rate': 'sum',
        'stock_dividend_total': 'sum',
        'dividend_plan': 'sum',
        'date': 'sum'
    }).reset_index()
    return gb


def _open_file(file_path=get_file_path_dividend_ths()):
    df = pd.read_csv(file_path, dtype={'symbol': str, })
    df['board_date'] = pd.to_datetime(df['board_date'])
    # 选出需要的数据列
    df = df[['symbol', 'name', 'date', 'board_date', 'dividend_plan', 'pretax_dividend_rate', 'stock_dividend_total', 'update_date']]
    # 得到分红数据的年份
    df['year_date'] = df['date'].apply(lambda x: x[:4])
    # 不分红应该要填充为0
    df['pretax_dividend_rate'].fillna(0, inplace=True)
    return df


if __name__ == '__main__':
    # average_dividend_rate_rank(year_count=10)
    df = query_dividend_rate()
    df = df[df['pretax_dividend_rate'] > 0.05]

    gb = df.groupby('symbol', group_keys=False).apply(lambda x: x.sort_values(by='year_date', ascending=False))

    gb['year_date'] = gb['year_date'].astype(int)
    gb = gb[gb['year_date'] > 2014]
    # gb.sort_values(by='pretax_dividend_rate', ascending=False, inplace=True)

    gb = gb.groupby('symbol').filter(lambda x: len(x) > 3)

    gb.reset_index(inplace=True, drop=True)
    print(gb.head(1000))
    print(len(gb))