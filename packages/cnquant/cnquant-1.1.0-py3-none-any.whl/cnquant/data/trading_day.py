"""
功能：
    1.生成交易日历，
    2.查询特定日期是否是交易日
"""

import datetime
from pathlib import Path
from typing import Union

import pandas as pd

from cnquant.core.get_web_data import get_web_json_content

from cnquant.config.config_data_path import (
    get_file_path_klines_dir,
    get_file_path_trading_day_dir,
)

"""
**********交易日历相关数据维护**********
最早数据可以从2005年开始
"""


def get_holidays_date(year):
    """
    中国法定节假日数据 自动每日抓取国务院公告
    https://github.com/NateScarlet/holiday-cn
    会保存数据
    """
    this_year_holiday_file = get_file_path_trading_day_dir() / f'holidays_{year}.txt'
    if not this_year_holiday_file.exists():
        print(f'{year}年节假日数据')

        base_url = 'https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{}.json'
        url = base_url.format(year)

        data = get_web_json_content(url)['days']
        df = pd.DataFrame(data)
        df = df[df['isOffDay'] == True]
        holidays = df['date'].tolist()

        with open(this_year_holiday_file, 'w') as f:
            for holiday in holidays:
                f.write(holiday + '\n')
    else:
        with open(this_year_holiday_file, 'r') as f:
            _holidays = f.readlines()
            holidays = [holiday.strip() for holiday in _holidays]
    return holidays


def get_this_year_holidays_date():
    return get_holidays_date(datetime.datetime.now().year)


def get_history_trading_day():
    """
    获取今年以前的交易日信息，
    数据来源上证指数的timestamp
    :return:
    """
    sz_index_file_path = get_file_path_klines_dir() / 'index_klines' / '上证指数.csv'
    df = pd.read_csv(sz_index_file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[df['timestamp'].dt.year < datetime.datetime.now().year]

    return df['timestamp'].dt.strftime('%Y-%m-%d').to_list()


def get_trading_days():
    """
    从深圳证券网站获取放假日期，保存为txt文件
    生成今年所有日历，剔除周末，剔除假期
    就得到今年的交易日列表
    :return:
    """
    # 打开今年的节假日文件
    year = datetime.datetime.now().year
    this_year_holiday_file = get_file_path_trading_day_dir() / f'holidays_{year}.txt'
    with open(this_year_holiday_file, 'r') as f:
        lines = f.readlines()
    holiday_list = [line.strip() for line in lines]

    # 生成今年的日期
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year, 12, 31)
    num_days = (end_date - start_date).days + 1
    this_year_date_list = [start_date + datetime.timedelta(days=i) for i in range(num_days)]

    # 去除周六周日
    no_weekend_date_list = [date for date in this_year_date_list if date.weekday() < 5]
    format_no_weekend_date_list = [i.strftime("%Y-%m-%d") for i in no_weekend_date_list]  # 格式化日期数据
    # 去除节假日
    trading_days = [i for i in format_no_weekend_date_list if i not in holiday_list]

    return trading_days


def get_all_trading_days():
    """
    获取A股历史上所有的交易日期
    """
    history_trading_day = get_history_trading_day()
    this_year_trading_day = get_trading_days()
    trading_days = history_trading_day + this_year_trading_day
    return trading_days


"""
**********从本地文件判断交易日**********
"""


def is_trading_day(timestamp: Union[str, datetime.date]) -> bool:
    """
    判断这个日期是否是交易日。
    实现：如果是今年的日期，则直接使用今年的交易日数据；如果是往年的日期，则需要得到历史所有的交易日数据
    """
    if isinstance(timestamp, str):  # 如果是字符串
        d_timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d')
        s_timestamp = timestamp
    else:  # 如果是datetime.date
        d_timestamp = timestamp
        s_timestamp = datetime.datetime.strftime(timestamp, '%Y-%m-%d')

    if d_timestamp.year == datetime.datetime.now().year:
        trading_days = get_trading_days()
    else:
        trading_days = get_all_trading_days()

    return s_timestamp in trading_days


def get_last_trading_day_date():
    """
    获取前一个交易日的日期
    比如说今天是2024-07-22.星期一，上一个交易日就是2024-02-19，星期五
    """
    yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)  # 昨天的日期

    while True:
        if is_trading_day(str(yesterday)):
            last_trading_day = yesterday
            break
        else:
            yesterday = yesterday - datetime.timedelta(days=1)

    return last_trading_day


# def get_latest_trading_day_date():
#     """
#     获取最近的交易日，如果是今天则返回今天的日期。如果今天不是交易日，则返回上一个交易日的日期
#     """
#     now = datetime.datetime.now()
#     today = now.date()
#
#     if is_trading_day(str(today)):
#         latest_trading_day = today
#     else:
#         latest_trading_day = get_last_trading_day_date()
#
#     return latest_trading_day


def data_update_date():
    """
    数据更新日期，收盘后。
    """
    now = datetime.datetime.now()
    today = now.date()

    # 今天不是交易日，这个日期就是前一个交易日
    if not is_trading_day(str(today)):
        update_date = get_last_trading_day_date()

    # 今天是交易日
    else:
        # 15点之前
        if now.hour < 15:
            update_date = get_last_trading_day_date()
        # 15点之后
        else:
            update_date = today

    return update_date


if __name__ == '__main__':
    # df = is_trading_days('2024-04-01', '2024-05-10')
    # print(df)

    # a = get_history_trading_day()
    # print(a)
    # print(len(a))

    # get_this_year_trading_day()

    # a = get_trading_days()
    # print(len(a))
    # for i in a:
    #     print(i)
    print(is_trading_day(datetime.datetime.now().date()))

    # get_holidays_date(2024)
    # a = get_latest_trading_day_date()
    # print(a)

    # a = data_update_date()
    # print(a)
