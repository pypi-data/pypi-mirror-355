import pandas as pd
from tqdm.auto import tqdm

from cnquant.core.format_symbol import format_symbol_point_exchange
from cnquant.core.get_web_data import get_web_json_content
from cnquant.core.name_symbol import symbol2name
from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.config.config_data_path import get_file_path_holder, get_file_path_free_holder, get_file_path_latest_holder, get_file_path_latest_free_holder
from cnquant.data.trading_day import data_update_date

"""
获取最新的日期的股东数据。
"""


def get_dates_base(symbol: str, base_url: str) -> list:
    f_symbol = format_symbol_point_exchange(symbol)
    url_holder_date = base_url.format(f_symbol)

    resp = get_web_json_content(url_holder_date)
    data = resp['result']['data']

    df = pd.DataFrame(data)
    df['END_DATE'] = pd.to_datetime(df['END_DATE']).dt.strftime('%Y-%m-%d')

    return df['END_DATE'].to_list()


def get_holder_dates(symbol: str) -> list:
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_EH_HOLDERSDATE&columns=SECUCODE%2CEND_DATE%2CIS_REPORTDATE&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize&sortTypes=-1&sortColumns=END_DATE&source=HSF10&client=PC'
    holder_dates = get_dates_base(symbol, base_url)
    return holder_dates


def get_free_holder_dates(symbol):
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_EH_FREEHOLDERSDATE&columns=SECUCODE%2CEND_DATE&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize&sortTypes=-1&sortColumns=END_DATE&source=HSF10&client=PC'
    df = get_dates_base(symbol, base_url)
    return df


def get_holder(symbol, end_date):
    base_url_holder = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_EH_HOLDERS&columns=SECUCODE%2CSECURITY_CODE%2CEND_DATE%2CHOLDER_RANK%2CHOLDER_NEW%2CHOLDER_NAME%2CSHARES_TYPE%2CHOLD_NUM%2CHOLD_NUM_RATIO%2CHOLD_NUM_CHANGE%2CCHANGE_RATIO&quoteColumns=&filter=(SECUCODE%3D%22{}%22)(END_DATE%3D%27{}%27)&pageNumber=1&pageSize=&sortTypes=1&sortColumns=HOLDER_RANK&source=HSF10&client=PC'
    f_symbol = format_symbol_point_exchange(symbol)
    url_holder = base_url_holder.format(f_symbol, end_date)

    resp = get_web_json_content(url_holder)
    data = resp['result']['data']

    df = pd.DataFrame(data)
    df.drop(columns=['SECUCODE'], inplace=True)
    df.rename(columns={'SECURITY_CODE': 'symbol'}, inplace=True)
    df['END_DATE'] = pd.to_datetime(df['END_DATE']).dt.date

    df.insert(loc=1, column='name', value=symbol2name(symbol))  # 第二列插入股票当前名称

    return df


def get_all_year_holder(symbol):
    end_dates = get_holder_dates(symbol)
    data_df = pd.DataFrame()
    for end_date in end_dates:
        df = get_holder(symbol, end_date)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def get_stocks_all_year_holder(symbols):
    data_df = pd.DataFrame()

    for symbol in tqdm(symbols):
        df = get_all_year_holder(symbol)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def save_all_stock_all_year_holder():
    symbols = get_all_symbols()
    df = get_stocks_all_year_holder(symbols)
    df.to_csv(get_file_path_holder(), index=False, encoding='utf-8-sig')


def get_a_stock_latest_holder(symbol):
    end_dates = get_holder_dates(symbol)
    latest_end_date = end_dates[0]

    df = get_holder(symbol, latest_end_date)
    return df


def save_all_stock_latest_holder():
    print('更新最新日期的十大股东数据')
    data_df = pd.DataFrame()
    symbols = get_all_symbols()

    for symbol in tqdm(symbols):
        df = get_a_stock_latest_holder(symbol)
        data_df = pd.concat([data_df, df], ignore_index=True)

    data_df['update_date'] = data_update_date()
    data_df.to_csv(get_file_path_latest_holder(), index=False, encoding='utf-8-sig')


def get_free_holder(symbol, end_date):
    base_url_free_holder = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_EH_FREEHOLDERS&columns=SECUCODE%2CSECURITY_CODE%2CEND_DATE%2CHOLDER_RANK%2CHOLDER_NEW%2CHOLDER_NAME%2CHOLDER_TYPE%2CSHARES_TYPE%2CHOLD_NUM%2CFREE_HOLDNUM_RATIO%2CHOLD_NUM_CHANGE%2CCHANGE_RATIO&quoteColumns=&filter=(SECUCODE%3D%22{}%22)(END_DATE%3D%27{}%27)&pageNumber=1&pageSize=&sortTypes=1&sortColumns=HOLDER_RANK&source=HSF10&client=PC'
    f_symbol = format_symbol_point_exchange(symbol)
    url_free_holder = base_url_free_holder.format(f_symbol, end_date)

    resp = get_web_json_content(url_free_holder)
    data = resp['result']['data']

    df = pd.DataFrame(data)
    df.drop(columns=['SECUCODE'], inplace=True)
    df.rename(columns={'SECURITY_CODE': 'symbol'}, inplace=True)
    df['END_DATE'] = pd.to_datetime(df['END_DATE']).dt.date

    df.insert(loc=1, column='name', value=symbol2name(symbol))  # 第二列插入股票当前名称

    return df


def get_all_year_free_holder(symbol):
    end_dates = get_free_holder_dates(symbol)
    data_df = pd.DataFrame()
    for end_date in end_dates:
        df = get_free_holder(symbol, end_date)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def get_stocks_all_year_free_holder(symbols):
    data_df = pd.DataFrame()

    for symbol in tqdm(symbols):
        df = get_all_year_free_holder(symbol)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def save_all_stock_all_year_free_holder():
    symbols = get_all_symbols()
    df = get_stocks_all_year_free_holder(symbols)
    df.to_csv(get_file_path_free_holder(), index=False, encoding='utf-8-sig')


def get_a_stock_latest_free_holder(symbol):
    end_dates = get_free_holder_dates(symbol)
    latest_end_date = end_dates[0]

    df = get_free_holder(symbol, latest_end_date)
    return df


def save_all_stock_latest_free_holder():
    print('更新最新日期的十大流通股东数据')
    data_df = pd.DataFrame()
    symbols = get_all_symbols()

    for symbol in tqdm(symbols):
        try:
            df = get_a_stock_latest_free_holder(symbol)
        except TypeError:
            print(f'{symbol}没有十大流通股东的数据')
            df = pd.DataFrame()
        data_df = pd.concat([data_df, df], ignore_index=True)

    data_df['update_date'] = data_update_date()
    data_df.to_csv(get_file_path_latest_free_holder(), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    # save_all_stock_latest_holder()
    save_all_stock_latest_free_holder()
