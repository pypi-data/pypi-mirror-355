from typing import Union, List

from lxml import etree
import pandas as pd
from tqdm.auto import tqdm

from cnquant.core.concat_dfs import concat_dfs
from cnquant.core.name_symbol import symbol2name
from cnquant.core.get_web_data import get_web_content
from cnquant.data.symbol.get_symbols import get_all_symbols


def parse_primary_operate_ths(resp) -> tuple:
    # 数据解析xpath
    html = resp.content.decode('gbk')
    tree = etree.HTML(html)
    column_list = tree.xpath('//*[@id="intro"]/div[2]/div/ul/li/span/text()')
    data_list = tree.xpath('//*[@id="intro"]/div[2]/div/ul/li/p/text()')

    # 去除表头的：
    column_list = [column.replace('：', '') for column in column_list]
    # 去除数据的\n\t
    data_list = [data.replace('\n', '').replace('\t', '').replace(' ', '') for data in data_list]

    return column_list, data_list


def get_stock_primary_operate_ths(symbol: str) -> pd.DataFrame:
    """
    获取一个股票的主营介绍数据
    """
    url = f'https://basic.10jqka.com.cn/{symbol}/operate.html'

    resp = get_web_content(url)
    column_list, data_list = parse_primary_operate_ths(resp)

    df = pd.DataFrame([data_list], columns=column_list)
    df['symbol'] = symbol
    df['name'] = symbol2name(symbol)

    # 排序一下
    df = df[['symbol', 'name', '主营业务', '产品类型', '产品名称', '经营范围']]

    return df


def get_stocks_primary_operate_ths(symbols: Union[str, List[str]]) -> pd.DataFrame:
    print(f'正在更新主营业务数据...')

    if isinstance(symbols, str):
        symbols = [symbols]

    df = concat_dfs(func=get_stock_primary_operate_ths, datas=symbols)
    return df


def save_all_stocks_primary_operate():
    from cnquant.config.config_data_path import get_file_path_main_business_ths

    print("更新股票主营业务【同花顺】...")

    symbols = get_all_symbols()
    df = get_stocks_primary_operate_ths(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_main_business_ths(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_stocks_primary_operate()
