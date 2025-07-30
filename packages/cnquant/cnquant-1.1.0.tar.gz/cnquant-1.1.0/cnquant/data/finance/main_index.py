"""
主要财务指标
"""
from typing import Union, List

import pandas as pd
from tqdm.auto import tqdm

from cnquant.core.concat_dfs import concat_dfs
from cnquant.core.get_web_data import get_web_json_content
from cnquant.core.format_symbol import format_symbol_point_exchange
from cnquant.config.config_columns import FINANCE_MAIN_INDEX_COLUMNS
from cnquant.config.config_data_path import get_file_path_finance_main_index
from cnquant.data.symbol.get_symbols import get_all_symbols


def get_finance_main_index(symbol):
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/get?type=RPT_F10_FINANCE_MAINFINADATA&sty=APP_F10_MAINFINADATA&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&p=1&ps&sr=-1&st=REPORT_DATE&source=HSF10&client=PC'
    f_symbol = format_symbol_point_exchange(symbol)
    url = base_url.format(f_symbol)

    # 获取数据
    data = get_web_json_content(url)['result']['data']
    df = pd.DataFrame(data)

    # 删除非不需要的列
    df.drop(columns=['SECUCODE', 'ORG_CODE', 'SECURITY_TYPE_CODE', 'ORG_TYPE', 'NOTICE_DATE', 'UPDATE_DATE', 'REPORT_TYPE', 'CURRENCY', 'REPORT_DATE_NAME',
                     'TOTALDEPOSITS',
                     'GROSSLOANS',
                     'LTDRR',
                     'NEWCAPITALADER', 'HXYJBCZL', 'NONPERLOAN',
                     'BLDKBBL', 'NZBJE', 'TOTAL_ROI', 'NET_ROI', 'EARNED_PREMIUM',
                     'COMPENSATE_EXPENSE', 'SURRENDER_RATE_LIFE', 'SOLVENCY_AR', 'JZB',
                     'JZC', 'JZBJZC', 'ZYGPGMJZC', 'ZYGDSYLZQJZB', 'YYFXZB', 'JJYWFXZB',
                     'ZQZYYWFXZB', 'ZQCXYWFXZB', 'RZRQYWFXZB', 'EPSJBTZ', 'BPSTZ',
                     'MGZBGJTZ', 'MGWFPLRTZ', 'MGJYXJJETZ', 'ROEJQTZ', 'ZZCJLLTZ', 'ZCFZLTZ',
                     'REPORT_YEAR', 'ROIC', 'ROICTZ', 'NBV_LIFE', 'NBV_RATE',
                     'NHJZ_CURRENT_AMT', 'DJD_TOI_YOY', 'DJD_DPNP_YOY', 'DJD_DEDUCTDPNP_YOY',
                     'DJD_TOI_QOQ', 'DJD_DPNP_QOQ', 'DJD_DEDUCTDPNP_QOQ', 'XSMLL_TB'
                     ], inplace=True)
    df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE']).dt.date
    df.rename(columns=FINANCE_MAIN_INDEX_COLUMNS, inplace=True)

    return df


def get_finance_main_indexes(symbols: Union[str, List[str]]):
    if isinstance(symbols, str):
        symbols = [symbols]
    df = concat_dfs(func=get_finance_main_index, datas=symbols)
    return df


def save_all_finance_main_index():
    print("更新股票财务分析--主要指标【东方财富】...")

    symbols = get_all_symbols()
    df = get_finance_main_indexes(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_finance_main_index(), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    save_all_finance_main_index()
