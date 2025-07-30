import pandas as pd
from cnquant.config.config_data_path import get_file_path_symbols_names


def name2symbol(name):
    # 打开股票代码名称文件
    df = pd.read_csv(get_file_path_symbols_names(), dtype={'symbol': str})

    print(df)
    print(name)

    # 含有这个字符的匹配
    condition1 = df['name'].str.contains(name)
    symbol = df.loc[condition1, 'symbol'].item()
    return symbol


def symbol2name(symbol):
    # 打开股票代码名称文件
    df = pd.read_csv(get_file_path_symbols_names(), dtype={'symbol': str})

    # 查看name
    return df.loc[df['symbol'] == symbol, 'name'].item()


if __name__ == '__main__':
    # print(symbol2name("600519"))
    print(name2symbol("格力电器"))
