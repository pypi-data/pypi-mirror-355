"""
1、计算各个股东持股总市值，以及排名
2、查询特定股东持股信息
3、查看特定股票的股东
"""
from decimal import Decimal
from pathlib import Path
from typing import Union, List

import pandas as pd
from tqdm.auto import tqdm

from cnquant.config.config_data_path import get_file_path_latest_holder, get_file_path_latest_free_holder, get_file_path_temp_dir
from cnquant.data.market_data import get_market_data_xq
from cnquant.data.symbol.get_symbols import get_all_symbols


def get_holder_total_capital_rank(gd_type='十大股东'):
    """
    1、计算各个股东持股总市值，以及排名
    """
    df, price_df = _open_files(gd_type)

    holder_names = df['HOLDER_NAME'].values.tolist()  # 获取股东名字列表
    holder_names = list(set(holder_names))  # 股东名字去重

    # 测试数据
    # holder_names = ['中央汇金投资有限责任公司']

    holder_values = []  # 列表存储每个股东持仓市值的数据
    # 逐个查询
    for holder in tqdm(holder_names):
        # 复制出来这个股东的所有持股数据，避免对源数据的影响
        holder_df = df[df['HOLDER_NAME'] == holder].copy()

        # 合并名称价格数据
        holder_df = pd.merge(left=holder_df, right=price_df, on='symbol')
        # 计算持仓市值
        holder_df['hold_value'] = holder_df['HOLD_NUM'] * holder_df['price']
        holder_df['END_DATE'] = pd.to_datetime(holder_df['END_DATE'])
        # 持仓市值求和，单位转为亿元
        holder_value = holder_df['hold_value'].sum() / 100000000
        holder_value = Decimal(holder_value).quantize(Decimal('0.0000'))
        # 保存数据到列表里面
        holder_values.append({'holder_name': holder,
                              'hold_value': holder_value})
    # 转为df
    holder_values_df = pd.DataFrame(holder_values)
    # 排名
    holder_values_df.sort_values(by=['hold_value'], inplace=True, ascending=False, ignore_index=True)

    # 保存缓存文件
    holder_values_df.to_csv(get_file_path_temp_dir() / f'各个股东持股总市值及排名_{gd_type}.csv', index=False, encoding='utf_8_sig')

    return holder_values_df


def query_holders_hold_stocks(holder_names: Union[str, List[str]], gd_type='十大股东'):
    """
    2、查询特定股东持股信息
    """
    if isinstance(holder_names, str):
        holder_names = [holder_names]

    df, price_df = _open_files(gd_type)

    # 提取股东名称列表
    all_holder_names = df['HOLDER_NAME'].values.tolist()
    # 股东去重
    all_holder_names = list(set(all_holder_names))
    # 提取包含特定字符的内容
    holders = [item for item in all_holder_names if any(s in item for s in holder_names)]

    holders_df = pd.DataFrame()  # 保存持股数据

    # 逐个查询
    for holder in tqdm(holders):
        holder_df = df[df['HOLDER_NAME'] == holder].copy()

        # 合并名称价格数据
        holder_df = pd.merge(left=holder_df, right=price_df, on='symbol')

        # 计算持仓市值
        holder_df['hold_value'] = holder_df['HOLD_NUM'] * holder_df['price'] / 100000000.0
        holder_df['END_DATE'] = pd.to_datetime(holder_df['END_DATE'])

        holders_df = holders_df.append(holder_df, ignore_index=True)

    # 按持仓市值排名
    holders_df.sort_values(by=['hold_value'], ascending=False, inplace=True, ignore_index=True)
    return holders_df


def _open_files(gd_type):
    if gd_type == '十大股东':
        data_file = get_file_path_latest_holder()
    else:
        data_file = get_file_path_latest_free_holder()

    df = pd.read_csv(data_file, dtype={'symbol': str})
    df.drop(columns='update_date', inplace=True)

    symbols = get_all_symbols()
    price_df = get_market_data_xq(symbols)
    price_df.rename(columns={'current': 'price'}, inplace=True)
    price_df = price_df[['symbol', 'price', 'market_capital', 'float_market_capital', 'timestamp']]
    price_df['market_capital'] = price_df['market_capital'] / 100000000.0
    price_df['float_market_capital'] = price_df['float_market_capital'] / 100000000.0

    return df, price_df


def query_stock_holders(symbol, gd_type='十大股东') -> pd.DataFrame:
    df, price_df = _open_files(gd_type)
    df = df[df['symbol'] == symbol]

    price = price_df.loc[price_df['symbol'] == symbol, 'price'].values[0]

    df['price'] = price
    df['value'] = df['HOLD_NUM'] * df['price'] / 100000000.0

    df.reset_index(drop=True, inplace=True)
    return df


if __name__ == '__main__':
    # df = get_holder_total_capital_rank(gd_type='十大流通股东')
    # df = query_holders_hold_stocks(holder_names=['小米', '王传福'], gd_type='十大流通股东')
    df = query_stock_holders('600519', gd_type='十大流通股东')
    print(df)
