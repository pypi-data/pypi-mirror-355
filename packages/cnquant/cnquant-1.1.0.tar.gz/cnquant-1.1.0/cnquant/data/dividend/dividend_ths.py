import pandas as pd
import lxml
from lxml import etree
from typing import Union, List
from tqdm.auto import tqdm

from cnquant.core.api import (
    get_web_json_content,
    get_web_content,
)
from cnquant.core.concat_dfs import concat_dfs
from cnquant.data.api import get_all_symbols
from cnquant.config.config_data_path import get_file_path_dividend_ths

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.expand_frame_repr', False)


def __get_market_id_name(symbol: str):
    base_url = 'https://basic.10jqka.com.cn/{}/'
    url = base_url.format(symbol)

    response = get_web_content(url).content.decode('gbk')
    tree = etree.HTML(response)
    market_id = tree.xpath('//*[@id="marketId"]/@value')[0]
    name = tree.xpath('//*[@id="stockName"]/@value')[0]
    return market_id, name


def get_company_dividend_ths(symbol: str) -> pd.DataFrame:
    market_id, name = __get_market_id_name(symbol)

    base_url = 'https://basic.10jqka.com.cn/basicapi/finance/dividends/v1/programme?code={}&market={}&showDividend=0&size=0&page=1'
    url = base_url.format(symbol, market_id)

    # 获取数据
    try:
        resp = get_web_json_content(url)
        data = resp['data']['page_result']['data']

        df = pd.DataFrame(data)
        df.insert(loc=0, column='symbol', value=symbol)  # 第一列插入股票代码
        df.insert(loc=1, column='name', value=name)  # 第二列插入股票当前名称
    except TypeError:
        print(f'{symbol}没有分红信息')
        df = pd.DataFrame()
    finally:
        return df


def get_companies_dividend_ths(symbols: Union[str, List[str]]) -> pd.DataFrame:
    if isinstance(symbols, str):
        symbols = [symbols]

    df = concat_dfs(func=get_company_dividend_ths, datas=symbols)
    return df


def save_all_companies_dividend_ths():
    print("更新股票分红数据【同花顺】...")

    symbols = get_all_symbols()
    df = get_companies_dividend_ths(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_dividend_ths(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    # df = get_company_dividend_ths('000001')
    # print(df)
    save_all_companies_dividend_ths()




