import pandas as pd
from tqdm.auto import tqdm

from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.core.get_web_data import get_web_json_content
from cnquant.core.format_symbol import format_symbol_point_exchange
from cnquant.core.name_symbol import symbol2name
from cnquant.config.config_data_path import get_file_path_business_scope


def get_business_scope(symbol):
    f_symbol = format_symbol_point_exchange(symbol)
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_HSF9_BASIC_ORGINFO&columns=SECUCODE%2CSECURITY_CODE%2CBUSINESS_SCOPE&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize&sortTypes=&sortColumns=&source=HSF10&client=PC'
    url = base_url.format(f_symbol)

    data = get_web_json_content(url)['result']['data']

    df = pd.DataFrame(data)

    # 删除非不需要的列
    df.drop(columns=['SECUCODE'], inplace=True)
    df.rename(columns={'SECURITY_CODE': 'symbol'}, inplace=True)
    df.insert(1, 'name', symbol2name(symbol))

    return df


def get_business_scopes(symbols):
    if isinstance(symbols, str):
        symbols = [symbols]
    data_df = pd.DataFrame()
    for symbol in tqdm(symbols):
        df = get_business_scope(symbol)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def save_all_business_scope():
    print("更新股票营业范围【东方财富】...")

    symbols = get_all_symbols()
    df = get_business_scopes(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_business_scope(), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    save_all_business_scope()


