"""
从同花顺F10,获取申万行业
"""
from typing import List, Union

import pandas as pd
from lxml import etree
from tqdm.auto import tqdm

from cnquant.config.config_data_path import get_file_path_sw_industry_classification
from cnquant.core.get_web_data import get_web_content
from cnquant.core.name_symbol import symbol2name
from cnquant.data.symbol.get_symbols import get_all_symbols


def parse_stock_sw_industry_classification(symbol: str) -> tuple:
    """
    获取个股的申万行业分类，以及主营业务
    """
    resp = get_web_content(f'https://basic.10jqka.com.cn/{symbol}/company.html')

    html = resp.content.decode('gbk')
    tree = etree.HTML(html)
    # 申万行业分类
    sw_industry_classification = tree.xpath('//*[@id="detail"]/div/table/tbody/tr[2]/td[2]/span/text()')[0]
    # 主营业务
    main_business = tree.xpath('//*[@id="detail"]/div/div/table/tbody/tr[1]/td/span/text()')[0]
    # 产品名称
    product_name = tree.xpath('//*[@id="detail"]/div/div/table/tbody/tr[2]/td/span/span/text()')[0]
    product_name = product_name.strip().replace('\t', '')  # 去掉开头结尾控股，\n, \t
    return sw_industry_classification, main_business, product_name


def get_stocks_sw_industry_classification(symbols: Union[str, List[str]]) -> List[dict]:
    if isinstance(symbols, str):
        symbols = [symbols]

    stocks_sw_industry_classification = []
    for symbol in tqdm(symbols):
        stock_sw_industry_classification, main_business, product_name = parse_stock_sw_industry_classification(symbol)
        stocks_sw_industry_classification.append({'symbol': symbol,
                               'name': symbol2name(symbol),
                               'sw_industry_classification': stock_sw_industry_classification,
                               'main_business': main_business,
                               'product_name': product_name,
                               })
    return stocks_sw_industry_classification


def save_all_stocks_sw_industry_classification() -> None:
    symbols = get_all_symbols()

    data = get_stocks_sw_industry_classification(symbols)
    df = pd.DataFrame(data)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_sw_industry_classification(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_stocks_sw_industry_classification()
