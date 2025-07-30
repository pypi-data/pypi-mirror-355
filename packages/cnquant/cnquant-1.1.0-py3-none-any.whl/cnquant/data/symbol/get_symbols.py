import os
import pandas as pd

from cnquant.data.symbol.get_sh_symbols import get_sh_a_symbols
from cnquant.data.symbol.get_sz_symbols import get_sz_a_symbols
from cnquant.data.symbol.get_bz_symbols import get_bz_symbols
from cnquant.config.config_data_path import get_file_path_symbols_names
from cnquant.data.trading_day import data_update_date


def get_all_symbols_from_gw() -> pd.DataFrame:
    """
    获取三市最新的所有股票代码及股票名称数据（不包括退市数据）官网获取
    """
    # 上证数据
    df1 = get_sh_a_symbols()
    df2 = get_sz_a_symbols()
    df3 = get_bz_symbols()

    df = pd.concat([df1, df2, df3], ignore_index=True)
    return df


def save_all_symbols_to_csv() -> None:
    """
    保存三市股票代码数据
    """
    print('股票代码数据更新...')
    df = get_all_symbols_from_gw()

    # 数据更新日期
    df['update_date'] = data_update_date()
    df.to_csv(get_file_path_symbols_names(), index=False, encoding='utf_8_sig')


"""
******************
本地文件读取
******************
"""


def get_all_symbols() -> list:
    if not os.path.exists(get_file_path_symbols_names()):
        save_all_symbols_to_csv()

    df = pd.read_csv(get_file_path_symbols_names(), dtype={'symbol': str})
    return df['symbol'].tolist()


def get_all_symbols_and_names() -> pd.DataFrame:
    if not os.path.exists(get_file_path_symbols_names()):
        save_all_symbols_to_csv()

    df = pd.read_csv(get_file_path_symbols_names(), dtype={'symbol': str})
    return df


def get_name_from_symbol(symbol: str) -> str:
    if not os.path.exists(get_file_path_symbols_names()):
        save_all_symbols_to_csv()

    df = pd.read_csv(get_file_path_symbols_names(), dtype={'symbol': str})
    name = df.loc[df['symbol'] == symbol, 'name'].item()
    return name


if __name__ == '__main__':
    # print(get_all_symbols())
    save_all_symbols_to_csv()
