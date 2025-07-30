from typing import Union, List

import pandas as pd
from tqdm.auto import tqdm

from cnquant.core.api import (
    get_web_json_content,
    format_symbol_point_exchange,
)
from cnquant.core.concat_dfs import concat_dfs
from cnquant.data.api import get_all_symbols
from cnquant.config.config_data_path import get_file_path_ipos_information

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option('display.expand_frame_repr', False)


def get_ipo_information(symbol: str) -> pd.DataFrame:
    f_symbol = format_symbol_point_exchange(symbol)
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_PCF10_ORG_ISSUEINFO&columns=ALL&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize=1&sortTypes=&sortColumns=&source=HSF10&client=PC'
    url = base_url.format(f_symbol)
    # 获取网络数据
    data = get_web_json_content(url)['result']['data']
    df = pd.DataFrame(data)
    df.rename(columns={'SECURITY_CODE': 'symbol'}, inplace=True)
    df.drop(columns=['SECUCODE'], inplace=True)
    return df


def get_ipos_information(symbols: Union[str, List[str]]) -> pd.DataFrame:
    if isinstance(symbols, str):
        symbols = [symbols]

    df = concat_dfs(func=get_ipo_information, datas=symbols)
    return df


def save_all_ipos_information() -> None:
    print("更新股票IPO数据【东方财富】...")

    symbols = get_all_symbols()
    df = get_ipos_information(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_ipos_information(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_ipos_information()
