"""
从同花顺获取公司实际控制人：symbol, name, 控制股东, 实际控制人, 最终控制人
"""
import pandas as pd
from lxml import etree
from tqdm.auto import tqdm

from cnquant.core.api import get_web_content
from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.config.config_data_path import get_file_path_actual_controller, get_file_path_symbols_names


def get_actual_controller(symbol):
    url = f'https://basic.10jqka.com.cn/{symbol}/holder.html'
    resp = get_web_content(url)

    # 数据解析xpath
    html = resp.content.decode('gbk')
    tree = etree.HTML(html)
    data = tree.xpath('//*[@id="holdlevel"]/div[2]/table/tbody/tr/td')

    data_dict = {}

    for item in data:
        data_key = item.xpath('./span[1]/text()')[0].split('：')[0]
        data_value = item.xpath('./span[2]/span/text()') + item.xpath('./text()')
        data_value = [x.replace('\n', '').replace('\t', '') for x in data_value if x.strip()]
        data_value = ','.join(data_value)

        data_dict[data_key] = data_value
    data_dict['symbol'] = symbol

    return data_dict


def get_actual_controllers(symbols):
    data_list = []

    for symbol in tqdm(symbols):
        a = get_actual_controller(symbol)  # 603886
        data_list.append(a)
    df = pd.DataFrame(data_list)
    df.insert(0, 'symbol', df.pop('symbol'))

    name_df = pd.read_csv(get_file_path_symbols_names(), dtype={'symbol': str})
    name_df = name_df[['symbol', 'name']]

    new_df = pd.merge(df, name_df, on='symbol', how='left')
    new_df.insert(1, 'name', new_df.pop('name'))

    return new_df


def save_all_actual_controller():
    print("更新股票实际控制人数据【同花顺】...")

    symbols = get_all_symbols()
    df = get_actual_controllers(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_actual_controller(), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    save_all_actual_controller()
