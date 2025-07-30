"""
日k线数据，分钟数据
前复权、不复权、后复权：0是不复权，1是前复权【炒股软件用的多】，2是后复权【量化用的多】
"""
import json
import shutil
from pathlib import Path

import pandas as pd
import requests
from tqdm.auto import tqdm

from cnquant.core.format_symbol import format_number_point_symbol
from cnquant.core.get_web_data import get_klines_em
from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.config.config_data_path import get_file_path_stock_kines_dir, get_file_path_temp_dir

KLINE_TYPE = {
    '101': '日K线'
}
FQ_TYPE = {
    '0': '不复权',
    '1': '前复权',
    '2': '后复权',
}

def get_stock_klines(symbol, kline_type, fq_type):
    f_symbol = format_number_point_symbol(symbol)
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'beg': '0',
        'end': '20500101',
        'rtntype': '6',
        'secid': f_symbol,
        'klt': kline_type,
        'fqt': fq_type,
    }

    # 获取数据
    resp = get_klines_em(url, params)
    data = resp['data']['klines']
    format_data = [line.split(',') for line in data]
    df = pd.DataFrame(format_data, columns=['timestamp', 'open', 'close', 'high', 'low',
                                            'volume', 'amount', 'amplitude', 'percent', 'change', 'turnover_rate'])
    df.insert(loc=0, column='symbol', value=symbol)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.date
    return df


def get_stocks_klines(symbols, kline_type, fq_type):
    """
    文件太大了
    :param symbols:
    :param kline_type:
    :param fq_type:
    :return:
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    data_df = pd.DataFrame()
    for symbol in tqdm(symbols):
        df = get_stock_klines(symbol, kline_type, fq_type)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def save_all_stocks_klines(kline_type, fq_type):

    a = input('是否需要清除缓存数据？输入y清除，n不清除：')
    if a == 'y':
        shutil.rmtree(get_file_path_temp_dir())
        get_file_path_temp_dir().mkdir(exist_ok=True, parents=True)

    symbols = get_all_symbols()
    # 读取缓存文件夹的目录，获取股票列表
    file_names = [x.name.split('.')[0] for x in get_file_path_temp_dir().glob('*') if x.is_file()]
    # 删除已经存在的股票列表
    symbols = [symbol for symbol in symbols if symbol not in file_names]

    for symbol in tqdm(symbols):
        df = get_stock_klines(symbol, kline_type, fq_type)

        # 保存临时文件
        temp_path = get_file_path_temp_dir() / f'{symbol}.csv'
        df.to_csv(temp_path, index=False, encoding='utf-8')

    file_path = get_file_path_stock_kines_dir() / f'{KLINE_TYPE[kline_type]}_{FQ_TYPE[fq_type]}.csv'
    # 读取临时文件，然后存为一个文件
    data_df = pd.DataFrame()
    files = [x for x in get_file_path_temp_dir().iterdir()]
    print("\n合并数据中....\n")
    for file in tqdm(files):
        temp_df = pd.read_csv(file, dtype={'symbol': str})
        data_df = pd.concat([data_df, temp_df], ignore_index=True)
    data_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    # 删除缓存数据
    for file in files:
        shutil.rmtree(file)


if __name__ == '__main__':
    kline_type = '101'
    fq_type = '1'
    save_all_stocks_klines(kline_type, fq_type)
