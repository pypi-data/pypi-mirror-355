"""
根据公司基本信息里的注册地，获取市、区县
"""
import pandas as pd

from cnquant.config.config_data_path import get_file_path_companies_information, get_file_path_companies_location
from cnquant.core.parse_address import parse_address


def save_all_companies_location():
    """
    根据公司基本信息里的注册地，获取市、区县
    :return:
    """
    df = pd.read_csv(get_file_path_companies_information(), dtype={'symbol': str})
    df = df[['symbol', 'name', 'province', 'REG_ADDRESS']]

    # 给apply添加进度条
    from tqdm import tqdm
    tqdm.pandas(desc='apply')

    # 获取市、区县
    df[['city', 'district']] = df['REG_ADDRESS'].progress_apply(lambda x: pd.Series(parse_address(x)))
    # 保存文件
    df = df[['symbol', 'name', 'province', 'city', 'district', 'REG_ADDRESS']]

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_companies_location(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_companies_location()
