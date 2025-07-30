import datetime
import pathlib
import time

import pandas as pd

from cnquant.data.trading_day import data_update_date, get_this_year_holidays_date
from cnquant.config.config_data_path import *


def _update_data(file_path: pathlib.Path, func):
    if not file_path.exists():
        func()
    else:
        df = pd.read_csv(file_path)
        update_date = df['update_date'].iloc[0]

        # 如果更新时间小于最近的收盘交易日，则更新数据
        if update_date < str(data_update_date()):
            func()
        else:
            print(f'{file_path}：数据已经是最新')


def update_dividend_ths():
    from cnquant.data.dividend.dividend_ths import save_all_companies_dividend_ths

    file_path = get_file_path_dividend_ths()
    _update_data(file_path, save_all_companies_dividend_ths)


def update_symbols():
    from cnquant.data.symbol.get_symbols import save_all_symbols_to_csv

    file_path = get_file_path_symbols_names()
    _update_data(file_path, save_all_symbols_to_csv)


def update_history_name():
    from cnquant.data.history_name import save_all_history_name

    file_path = get_file_path_history_name()
    _update_data(file_path, save_all_history_name)


def update_index_klines():
    """
    更新指数日K线数据
    这个特殊，不能改
    """
    from cnquant.config.config_data_path import get_file_path_index_klines_dir
    from cnquant.data.klines.index_klines_em import save_all_index_day_klines
    sh_index_klines_file = get_file_path_index_klines_dir() / '上证指数.csv'

    if not sh_index_klines_file.exists():
        save_all_index_day_klines()
    else:
        df = pd.read_csv(sh_index_klines_file)
        update_date = df['timestamp'].iloc[-1]

        # 如果更新时间小于最近的收盘交易日，则更新数据
        if update_date < str(data_update_date()):
            save_all_index_day_klines()
        else:
            print('指数日K线数据已经是最新')


def update_latest_holder():
    """
    更新最新日期的十大股东数据
    """
    from cnquant.data.holder.holder import save_all_stock_latest_holder

    file_path = get_file_path_latest_holder()
    _update_data(file_path, save_all_stock_latest_holder)


def update_latest_free_holder():
    """
    更新最新日期的十大流通股东数据
    """
    from cnquant.data.holder.holder import save_all_stock_latest_free_holder

    file_path = get_file_path_latest_free_holder()
    _update_data(file_path, save_all_stock_latest_free_holder)


def update_holder_num():
    """
    更新股东数量数据
    """
    from cnquant.data.holder.holder_num import save_all_stock_holder_nums

    file_path = get_file_path_holder_num()
    _update_data(file_path, save_all_stock_holder_nums)


def update_finance_main_index():
    """
    更新财务分析--主要指标
    """
    from cnquant.data.finance.main_index import save_all_finance_main_index

    file_path = get_file_path_finance_main_index()
    _update_data(file_path, save_all_finance_main_index)


def update_ipo():
    """
    更新股票ipo数据
    """
    from cnquant.data.company.ipo_information import save_all_ipos_information

    file_path = get_file_path_ipos_information()
    _update_data(file_path, save_all_ipos_information)


def update_companies_information():
    """
    更新股票公司信息数据
    """
    from cnquant.data.company.company_information import save_all_companies_information

    file_path = get_file_path_companies_information()
    _update_data(file_path, save_all_companies_information)


def update_main_business():
    """
    更新股票主营业务【同花顺】
    """
    from cnquant.data.business.main_business_ths import save_all_stocks_primary_operate

    file_path = get_file_path_main_business_ths()
    _update_data(file_path, save_all_stocks_primary_operate)


def update_main_business_composition_analysis():
    """
    更新股票主营业务分析【东方财富】
    """
    from cnquant.data.business.main_business_composition_analysis import save_all_main_business_composition_analysis

    file_path = get_file_path_main_business_composition_analysis()
    _update_data(file_path, save_all_main_business_composition_analysis)


def update_actual_controller():
    """
    更新股票实际控制人数据【同花顺】
    """
    from cnquant.data.actual_controller import save_all_actual_controller

    file_path = get_file_path_actual_controller()
    _update_data(file_path, save_all_actual_controller)


def update_company_location():
    """
    更新股票城市数据【同花顺】
    """
    from cnquant.data.company.company_location import save_all_companies_location

    file_path = get_file_path_companies_location()
    _update_data(file_path, save_all_companies_location)


def update_sw_industry_classification():
    """
    更新股票城市数据【同花顺】
    """
    from cnquant.data.company.sw_industry_classification_ths import save_all_stocks_sw_industry_classification

    file_path = get_file_path_sw_industry_classification()
    _update_data(file_path, save_all_stocks_sw_industry_classification)


BASIC_FUNCTION_LIST = [
    # 节假日数据
    get_this_year_holidays_date,  # 获取今年节假日信息
    # 指数K线数据
    update_index_klines,
    # 股票代码数据
    update_symbols,
]

OTHER_FUNCTION_LIST = [
    # 股票历史名称
    update_history_name,

    # 股东分析
    update_latest_holder,
    update_latest_free_holder,
    update_holder_num,

    # 分红
    update_dividend_ths,

    # 财务分析主要指标
    update_finance_main_index,

    # 基本信息
    update_ipo,
    update_companies_information,
    update_company_location,
    update_sw_industry_classification,

    # 经营分析
    update_main_business,
    update_main_business_composition_analysis,

    # 实控人数据
    update_actual_controller,
]


def update_data():
    start = time.time()
    print('基础数据初始化中...')
    for func in BASIC_FUNCTION_LIST:
        func()
    print('基础数据初始化完毕！\n')

    print('更新其他数据中...')
    for func in OTHER_FUNCTION_LIST:
        func()
    print('数据更新完毕！\n')
    print(f'程序总共耗时%d小时%d分钟%s秒' % (seconds_to_hms(time.time() - start)))


"""
多线程更新数据
"""
def seconds_to_hms(seconds):
    hour, remainder = divmod(seconds, 3600)
    minute, second = divmod(remainder, 60)
    return int(hour), int(minute), int(second)


def multithread_update_data(thread_num=2):
    start = time.time()

    # 先更新必须的基础数据
    for func in BASIC_FUNCTION_LIST:
        func()

    from cnquant.core.run_multi_func import run_multithreaded
    run_multithreaded(OTHER_FUNCTION_LIST, thread_num)

    print(f'程序总共耗时%d小时%d分钟%s秒' % (seconds_to_hms(time.time() - start)))


if __name__ == '__main__':
    multithread_update_data()
