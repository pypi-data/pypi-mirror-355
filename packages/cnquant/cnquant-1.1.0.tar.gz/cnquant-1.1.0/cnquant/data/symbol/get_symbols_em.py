from typing import Union, List

import pandas as pd

import cnquant
from cnquant.core.get_web_data import get_klines_em
from cnquant.data.symbol.get_symbols import get_all_symbols


def get_symbols_em():
    url = 'https://48.push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': 1,
        'pz': 50000,  # 一页的股票数量
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'dect': 1,
        'wbp2u': '|0|0|0|web',
        'fid': 'f3',
        'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048',
        'fields': 'f12'  # f12: 股票代码
    }

    data = get_klines_em(url, params)['data']
    # symbol_num = data['total']
    symbol_data = data['diff']
    symbols = [list(i.values())[0] for i in symbol_data]
    return symbols


def get_delisted_symbols():
    """
    获取退市股票列表
    先获取东财所有A股的股票列表
    然后对比官网的股票列表，取差集，就是退市的股票
    :return:
    """
    symbols = get_symbols_em()
    gw_symbols = get_all_symbols()
    delisted_symbols = [symbol for symbol in symbols if symbol not in gw_symbols]
    return delisted_symbols


def get_stocks_name(symbols: Union[str, List[str]]):
    url = 'https://48.push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': 1,
        'pz': 50000,  # 一页的股票数量
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'dect': 1,
        'wbp2u': '|0|0|0|web',
        'fid': 'f3',
        'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048',
        'fields': 'f12,f14'  # f12: 股票代码, f14,股票名称
    }

    data = get_klines_em(url, params)['data']['diff']
    df = pd.DataFrame(data)
    df.columns = ['symbol', 'name']

    # 选取数据
    if isinstance(symbols, str):
        symbols = [symbols]
    df = df.loc[df['symbol'].isin(symbols)]
    df.reset_index(drop=True, inplace=True)
    return df


if __name__ == '__main__':
    symbols = get_delisted_symbols()
    df = get_stocks_name(symbols)
    print(df)

