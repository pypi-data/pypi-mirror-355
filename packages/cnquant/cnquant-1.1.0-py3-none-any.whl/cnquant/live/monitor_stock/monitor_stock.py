import datetime
import time
from typing import Union, List

import pandas as pd

from cnquant.data.market_data import get_live_price
from cnquant.data.symbol.get_symbols import get_all_symbols
from cnquant.utils.sendemail import send_email


def monitor_a_stocks(symbols: Union[str, List[str]], email, low_percent=-10.0, high_percent=10.0, abs_percent=10.0, heartbeat=5):
    """
    实时监控股票价格涨跌幅，超过10%，20%，30%以此类推发出警报，{股票名称：，股票价格：，涨跌幅：，时间：}，
    监控股票大幅波动
    :参数
    heartbeat: 监控心跳，默认是5s
    """
    target_symbols_data = {}  # {symbol: series}

    if isinstance(symbols, str):
        symbols = [symbols]

    while True:
        print('现在时间：%s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # 获取实时股票行情数据
        df = get_live_price(symbols)
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        percent_df = df[['symbol', 'name', 'percent', 'current', 'timestamp']]

        # 选出涨跌幅度大的股票
        target_df = percent_df[(percent_df['percent'] < low_percent) | (percent_df['percent'] > high_percent)]
        target_df_symbols = target_df['symbol'].to_list()

        # 有符合条件的股票
        content = []
        if len(target_df_symbols) > 0:
            for index, row in target_df.iterrows():
                symbol = row['symbol']

                # 如果不在target_symbols_data内
                if symbol not in list(target_symbols_data.keys()):
                    # 把这个series添加到target_symbols_data内
                    target_symbols_data[symbol] = row
                    # 邮件内容
                    content.append(row)
                else:
                    # 在target_symbols_data内，则对比一下涨跌幅的差值的绝对值，如果大于abs_percent，则发送邮件
                    old_percent = target_symbols_data[symbol]['percent']
                    new_percent = row['percent']
                    if abs(new_percent-old_percent) >= abs_percent:
                        # 把这个series替换到target_symbols_data内
                        target_symbols_data[symbol] = row
                        # 邮件内容
                        content.append(row)
            # 发送邮件
            content_df = pd.DataFrame(content)
            content_df.reset_index(drop=True, inplace=True)
            if not content_df.empty:
                print(content_df)
                send_email(email, title=','.join(content_df['name'].to_list()), content=content_df.to_string())
        else:
            print('没有符合条件的股票')

        time.sleep(heartbeat)
