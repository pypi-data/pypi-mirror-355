from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

from cnquant.config.config_index import INDEX_SYMBOLS
from cnquant.core.get_web_data import get_web_json_content
from cnquant.config.config_data_path import get_file_path_index_klines_dir


def get_klines(symbol, kline_type, fq_type, limit_type=50000):
    base_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={}&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt={}&fqt={}&end=20500101&lmt={}'
    url = base_url.format(symbol, kline_type, fq_type, limit_type)
    # 获取数据
    data = get_web_json_content(url)['data']['klines']
    format_data = [line.split(',') for line in data]
    # 格式化数据
    df = pd.DataFrame(format_data, columns=['timestamp', 'open', 'close', 'high', 'low',
                                            'volume', 'amount', 'amplitude', 'percent', 'change', 'turnover_rate'])
    # 添加名称及代码
    name = INDEX_SYMBOLS.get(symbol)
    df.insert(loc=0, column='name', value=name)

    return df


def get_index_day_klines(symbol, kline_type=101, fq_type=1, limit_type=50000):
    df = get_klines(symbol, kline_type, fq_type, limit_type)
    return df


def save_all_index_day_klines():
    print("指数K线更新中...")
    symbols = list(INDEX_SYMBOLS.keys())
    for symbol in tqdm(symbols):
        df = get_index_day_klines(symbol)

        file_path = get_file_path_index_klines_dir() / f'{INDEX_SYMBOLS.get(symbol)}.csv'
        df.to_csv(file_path, index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    save_all_index_day_klines()
