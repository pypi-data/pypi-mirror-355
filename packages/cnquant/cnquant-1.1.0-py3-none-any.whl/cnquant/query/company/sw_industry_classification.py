import pandas as pd

from cnquant.config.config_data_path import get_file_path_sw_industry_classification
from cnquant.data.market_data import get_all_market_data_em


def query_sw_industry_classification_company(**kwargs) -> pd.DataFrame:
    """
    查询特定行业的所有公司

    Parameters
    ----------
    df = query_shenwan_sorting_company(sw_industry_classification='燃气', main_business='自来水', product_name='自来水')

    Returns
    -------
    pd.DataFrame

    Examples
    --------
    >>> import cnquant as cq
    >>> df = query_sw_industry_classification_company(sw_industry_classification='燃气', main_business='自来水', product_name='自来水')
    >>> df

    """
    df = pd.read_csv(get_file_path_sw_industry_classification(), dtype={'symbol': str})
    data_df = pd.DataFrame()
    for key, value in kwargs.items():
        _df = df[df[key].str.contains(value)]
        data_df = pd.concat([data_df, _df], ignore_index=True)

    data_df.drop_duplicates(inplace=True)
    # df.reset_index(inplace=True, drop=True)
    return data_df


if __name__ == '__main__':
    # df = query_sw_industry_classification_company(sw_industry_classification='燃气', main_business='自来水', product_name='自来水')
    df = query_sw_industry_classification_company(main_business='人工智能', product_name='人工智能')

    price_df = get_all_market_data_em()
    price_df.drop(columns=['name'], inplace=True)

    data_df = pd.merge(df, price_df, how='left', on='symbol')

    data_df.sort_values(by=['market_capital'], ascending=False, inplace=True)
    data_df.reset_index(drop=True, inplace=True)

    print(data_df)


