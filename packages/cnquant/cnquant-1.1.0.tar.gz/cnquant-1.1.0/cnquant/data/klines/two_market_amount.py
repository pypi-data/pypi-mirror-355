from pathlib import Path
import pandas as pd
import mplfinance as mpf

from cnquant.config.config_data_path import get_file_path_index_klines_dir


def two_market_amount(kline_num=60):
    # 设置mplfinance的蜡烛颜色，up为阳线颜色，down为阴线颜色
    my_color = mpf.make_marketcolors(up='r',
                                     down='g',
                                     edge='inherit',
                                     wick='inherit',
                                     volume='inherit')
    # 设置图表的背景色
    my_style = mpf.make_mpf_style(marketcolors=my_color,
                                  figcolor='(0.82, 0.83, 0.85)',
                                  gridcolor='(0.82, 0.83, 0.85)')

    # 打开上证指数数据
    sh_index_file = get_file_path_index_klines_dir() / '上证指数.csv'
    sh_index_df = pd.read_csv(sh_index_file)
    sh_index_df.set_index('timestamp', inplace=True)
    # print(sh_index_df.tail())

    # 打开深成指数数据
    sz_index_file = get_file_path_index_klines_dir() / '深成指数.csv'
    sz_index_df = pd.read_csv(sz_index_file)
    sz_index_df.set_index('timestamp', inplace=True)
    # print(sz_index_df.tail())

    # 两列amount相加，然后单位换算成亿元
    result = sh_index_df['amount'] + sz_index_df['amount']
    # print(result)
    # print(type(result))
    sh_index_df['two_amount'] = result
    sh_index_df['two_amount'] = sh_index_df['two_amount'] / 100000000

    format_df = sh_index_df
    format_df = format_df[['open', 'high', 'low', 'close', 'two_amount']]
    format_df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    format_df.index = pd.to_datetime(format_df.index)
    format_df.index.name = 'Date'

    mpf.plot(data=format_df[-kline_num:], type='candle', style=my_style, volume=True)  # "yahoo"

    return format_df


if __name__ == '__main__':
    two_market_amount(kline_num=120)
