from typing import Union, List
import pandas as pd
from tqdm.auto import tqdm

from cnquant.core.api import (
    format_symbol_point_exchange,
    get_web_json_content,
    symbol2name,
)
from cnquant.data.api import get_all_symbols
from cnquant.config.config_data_path import get_file_path_holder_num


def get_holder_num(symbol, page_size=1000):
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_EH_HOLDERNUM&columns=SECUCODE%2CSECURITY_CODE%2CEND_DATE%2CHOLDER_TOTAL_NUM%2CTOTAL_NUM_RATIO%2CAVG_FREE_SHARES%2CAVG_FREESHARES_RATIO%2CHOLD_FOCUS%2CPRICE%2CAVG_HOLD_AMT%2CHOLD_RATIO_TOTAL%2CFREEHOLD_RATIO_TOTAL&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize={}&sortTypes=-1&sortColumns=END_DATE&source=HSF10&client=PC'
    f_symbol = format_symbol_point_exchange(symbol)
    url = base_url.format(f_symbol, page_size)

    resp = get_web_json_content(url)
    data = resp['result']['data']

    df = pd.DataFrame(data)
    df.drop(columns=['SECUCODE'], inplace=True)
    df.rename(columns={'SECURITY_CODE': 'symbol'}, inplace=True)
    df['END_DATE'] = pd.to_datetime(df['END_DATE']).dt.date
    df.insert(loc=1, column='name', value=symbol2name(symbol))  # 第二列插入股票当前名称

    return df


def get_holder_nums(symbols: Union[List[str], str]) -> pd.DataFrame:
    if isinstance(symbols, str):
        symbols = [symbols]
    all_df = pd.DataFrame()
    for symbol in tqdm(symbols):
        df = get_holder_num(symbol)
        all_df = pd.concat([all_df, df], ignore_index=True)
    return all_df


def save_all_stock_holder_nums():
    print('更新股东数量数据中...')

    symbols = get_all_symbols()
    df = get_holder_nums(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_holder_num(), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    save_all_stock_holder_nums()
