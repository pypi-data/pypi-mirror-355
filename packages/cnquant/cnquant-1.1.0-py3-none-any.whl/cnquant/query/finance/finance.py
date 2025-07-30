import pandas as pd

from cnquant.config.config_data_path import get_file_path_finance_main_index


def query_finance_main_index(timestamp, column='归属净利润(元)'):
    """
    查询特定日期的各种财务指标排名
    """
    df = pd.read_csv(get_file_path_finance_main_index(), dtype={'symbol': str})
    df.drop(columns=['扣非每股收益(元)'], inplace=True)

    # gb = df.groupby('symbol').apply(lambda x: x.iloc[0])  # 提取每个股票最新的财务数据
    gb = df[df['timestamp'] == timestamp]

    # 营业总收入排名一下
    gb = gb.sort_values(by=[column], ascending=False)
    gb.insert(2, column, gb.pop(column))
    gb.reset_index(drop=True, inplace=True)
    return gb


if __name__ == '__main__':
    df = query_finance_main_index(timestamp='2024-03-31', column='扣非净利润(元)')  # 2023-12-31, 2024-03-31, 毛利率(%), 净利率(%)
    print(df.head(100))
    print(len(df))
