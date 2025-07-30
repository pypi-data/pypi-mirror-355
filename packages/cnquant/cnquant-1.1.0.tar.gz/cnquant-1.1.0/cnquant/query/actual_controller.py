from typing import Union, List

import pandas as pd


def query_actual_controller_hold_stock(controller_names: Union[str, List[str]]) -> pd.DataFrame:
    """
    查询某些实控人持有哪些公司
    :param controller_names: 公司名称列表

    # 查询国有资产控股公司
    df = query_actual_controller_hold_stock(controller_names='国有资产')
    """
    if isinstance(controller_names, str):
        controller_names = [controller_names]

    from cnquant.config.config_data_path import get_file_path_actual_controller
    df = pd.read_csv(get_file_path_actual_controller(), dtype={'symbol': str})

    actual_controller_list = df['实际控制人'].to_list()
    actual_controller_list = list(set(actual_controller_list))
    # 提取包含特定字符的内容
    controllers = [item for item in actual_controller_list if any(s in item for s in controller_names)]

    return df[df['实际控制人'].isin(controllers)].reset_index(drop=True)


if __name__ == '__main__':
    # 查询国有资产控股公司
    df = query_actual_controller_hold_stock(controller_names='国有资产')

    # 打开地址文件
    from cnquant.config.config_data_path import get_file_path_companies_location
    location_df = pd.read_csv(get_file_path_companies_location(), dtype={'symbol': str})
    location_df.drop(columns='name', inplace=True)

    new_df = pd.merge(df, location_df, how='left', on='symbol')

    # new_df = new_df[new_df['province'].notnull() & new_df['province'].str.contains('河南')]
    # new_df = new_df[new_df['city'] == '北京市']

    new_df.reset_index(drop=True, inplace=True)
    print(new_df)
    print(len(new_df))

