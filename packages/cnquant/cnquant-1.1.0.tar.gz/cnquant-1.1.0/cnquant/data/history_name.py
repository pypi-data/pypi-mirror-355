"""
东方财富获取股票历史名称
"""
import pandas as pd
from tqdm.auto import tqdm

from cnquant.core.get_web_data import get_web_json_content
from cnquant.core.format_symbol import format_symbol_point_exchange
from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.config.config_data_path import get_file_path_history_name
from cnquant.data.trading_day import data_update_date


def get_history_name_em(symbol: str) -> pd.DataFrame:
    """
    # 获取股票历史名称
    :param symbol:
    :return:
    """
    # 格式化股票代码
    f_symbol = format_symbol_point_exchange(symbol)
    url = f'https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_IPO_ABSTOCK&columns=SECURITY_CODE,CHANGE_DATE,CHANGE_AFTER_FN,CHANGE_AFTER_AB,TRADE_MARKET_TYPE,RANK,SECUCODE&quoteColumns=&filter=(SECUCODE=%22{f_symbol}%22)&pageNumber=1&pageSize=100&sortTypes=1&sortColumns=CHANGE_DATE&source=QuoteWeb&client=WEB'
    # 获取网络数据
    resp = get_web_json_content(url=url)
    # 处理数据
    data = resp['result']['data']
    df = pd.DataFrame(data)

    df.rename(columns={'CHANGE_DATE': 'timestamp', 'CHANGE_AFTER_FN': 'name'}, inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.date
    df = df[['timestamp', 'name']]
    df.insert(loc=1, column='symbol', value=symbol)

    return df


def get_history_names_em(symbols: list) -> pd.DataFrame:
    if isinstance(symbols, str):
        symbols = [symbols]

    data_df = pd.DataFrame()
    for symbol in tqdm(symbols):
        df = get_history_name_em(symbol)
        data_df = pd.concat([data_df, df], ignore_index=True)
    return data_df


def save_all_history_name():
    print('股票历史名称更新中...')
    symbols = get_all_symbols()
    # 数据更新时间
    update_date = data_update_date()

    df = get_history_names_em(symbols)
    df['update_date'] = update_date

    df.to_csv(get_file_path_history_name(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_history_name()
