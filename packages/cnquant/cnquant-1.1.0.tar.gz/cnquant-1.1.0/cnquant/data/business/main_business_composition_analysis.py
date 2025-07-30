"""
更新主营业务分析【东方财富】
同花顺的搞不定
"""

import pandas as pd
from tqdm.auto import tqdm

from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.core.get_web_data import get_web_json_content
from cnquant.core.format_symbol import format_symbol_point_exchange
from cnquant.core.name_symbol import symbol2name
from cnquant.config.config_data_path import get_file_path_main_business_composition_analysis


def get_main_business_composition_analysis(symbol):
    f_symbol = format_symbol_point_exchange(symbol)
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_FN_MAINOP&columns=SECUCODE%2CSECURITY_CODE%2CREPORT_DATE%2CMAINOP_TYPE%2CITEM_NAME%2CMAIN_BUSINESS_INCOME%2CMBI_RATIO%2CMAIN_BUSINESS_COST%2CMBC_RATIO%2CMAIN_BUSINESS_RPOFIT%2CMBR_RATIO%2CGROSS_RPOFIT_RATIO%2CRANK&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize&sortTypes=-1%2C1%2C1&sortColumns=REPORT_DATE%2CMAINOP_TYPE%2CRANK&source=HSF10&client=PC&'
    url = base_url.format(f_symbol)
    try:
        data = get_web_json_content(url)['result']['data']
        df = pd.DataFrame(data)

        # 删除非不需要的列
        df.drop(columns=['SECUCODE', 'MAINOP_TYPE', 'RANK'], inplace=True)
        df.rename(columns={'SECURITY_CODE': 'symbol', 'REPORT_DATE': 'timestamp', 'ITEM_NAME': '主营构成',
                           'MAIN_BUSINESS_INCOME': '主营收入(元)', 'MBI_RATIO': '收入比例',
                           'MAIN_BUSINESS_COST': '主营成本(元)', 'MBC_RATIO': '成本比例',
                           'MAIN_BUSINESS_RPOFIT': '主营利润(元)', 'MBR_RATIO': '利润比例', 'GROSS_RPOFIT_RATIO': '毛利率(%)'},
                  inplace=True)
        df.insert(1, 'name', symbol2name(symbol))
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.date
    except KeyError:
        print(f'{symbol}没有数据')
        df = pd.DataFrame()
    return df


def get_main_business_composition_analysis_s(symbols):
    if isinstance(symbols, str):
        symbols = [symbols]
    data_df = pd.DataFrame()
    for symbol in tqdm(symbols):
        # print(symbol)
        df = get_main_business_composition_analysis(symbol)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def save_all_main_business_composition_analysis():
    print("更新股票主营业务分析【东方财富】...")

    symbols = get_all_symbols()
    df = get_main_business_composition_analysis_s(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_main_business_composition_analysis(), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    save_all_main_business_composition_analysis()
