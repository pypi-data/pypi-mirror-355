import pandas as pd
from typing import Union, List

from cnquant.core.format_symbol import format_symbol_point_exchange
from cnquant.core.get_web_data import get_web_json_content
from cnquant.core.concat_dfs import concat_dfs
from cnquant.data.api import get_all_symbols
from cnquant.config.config_data_path import get_file_path_dividend_em

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.expand_frame_repr', False)


def get_company_dividend(symbol: str, page_size=200) -> pd.DataFrame:
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_DIVIDEND_MAIN&columns=ALL&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize={}&sortTypes=-1&sortColumns=NOTICE_DATE&source=HSF10&client=PC'

    f_symbol = format_symbol_point_exchange(symbol)
    url = base_url.format(f_symbol, page_size)

    # 获取数据
    try:
        resp = get_web_json_content(url)
        data = resp['result']['data']

        df = pd.DataFrame(data)

        # 格式化数据
        df.drop(columns=['SECUCODE'], inplace=True)
        df.rename(columns={'SECURITY_CODE': 'symbol', 'SECURITY_NAME_ABBR': 'name'}, inplace=True)
    except TypeError:
        print(f'{symbol}没有分红信息')
        df = pd.DataFrame()
    finally:
        return df


def get_companies_dividend(symbols: Union[str, List[str]]) -> pd.DataFrame:
    if isinstance(symbols, str):
        symbols = [symbols]

    df = concat_dfs(func=get_company_dividend, datas=symbols)
    return df


def save_all_companies_dividend():
    symbols = get_all_symbols()
    df = get_companies_dividend(symbols)
    df.to_csv(get_file_path_dividend_em(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_companies_dividend()






