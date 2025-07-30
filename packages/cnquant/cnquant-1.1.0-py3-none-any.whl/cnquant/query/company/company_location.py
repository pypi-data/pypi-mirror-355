"""
功能：
1、根据公司信息获取市县区信息
2、所有城市上市公司数量排名
3、查询单个或者多个城市上市公司数量
"""

from typing import List, Union
import pandas as pd

from cnquant.config.config_data_path import (
    get_file_path_companies_location,
)

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.expand_frame_repr', False)


def rank_companies_number(location_type: str = 'province') -> pd.DataFrame():
    """
    获取城市上市公司数量排名
    :param location_type:province or city or district
    :return: 上市公司排名数据
    """
    df = pd.read_csv(get_file_path_companies_location(), dtype={'symbol': str})
    # 统计各城市上市公司数量
    s = df.groupby([location_type]).size()
    _s = s.sort_values(ascending=False)

    # 格式化数据
    _s.name = 'count'
    df = _s.to_frame()
    df.reset_index(inplace=True)
    df.index += 1

    return df


def query_companies_number(location: Union[str, List[str]] = '北京', location_type: str = 'province') -> pd.DataFrame():
    """
    查询城市的上市公司数量
    :param location_type: province or city or district
    :param location: str or list，城市字符串或列表
    :return:
    """
    if isinstance(location, str):
        location = [location]

    df = pd.read_csv(get_file_path_companies_location(), dtype={'symbol': str})
    # 统计各城市上市公司数量
    s = df.groupby([location_type]).size()

    _s = s[s.index.str.contains('|'.join(location))]

    # 格式化数据
    _s.name = 'count'
    df = _s.to_frame()
    df.reset_index(inplace=True)
    df.index += 1

    return df


def query_location_companies(location: Union[str, List[str]], location_type: str = 'city') -> pd.DataFrame():
    """
    查询某个省、市、区县的上市公司

    Parameters
    ----------
    location : str or list, 城市名称或者城市名称列表
    location_type: province or city or district, 省，市，或者区县，参数是英文：province, city or district

    Returns
    -------
    是一个pd.Dataframe()

    Examples
    --------
    >>> import cnquant as cq
    >>> df = cq.query_location_companies(location='信阳', location_type='city')
    >>> df
        symbol      name province    city district                        REG_ADDRESS update_date
    0  600285  羚锐制药     河南  信阳市     新县              河南省新县将军路666号  2024-07-26
    1  002321  华英农业     河南  信阳市   潢川县  河南省潢川县产业集聚区工业大道1号  2024-07-26
    """
    if isinstance(location, str):
        location = [location]

    df = pd.read_csv(get_file_path_companies_location(), dtype={'symbol': str})

    # 提取数据
    _df = df[df[location_type].notnull() & df[location_type].str.contains('|'.join(location))]
    _df.reset_index(inplace=True, drop=True)
    return _df
