import pandas as pd
from typing import Union, List

from cnquant.core.api import (
    get_web_json_content,
    format_symbol_point_exchange,
)
from cnquant.core.concat_dfs import concat_dfs
from cnquant.data.api import get_all_symbols
from cnquant.config.config_data_path import get_file_path_companies_information

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option('display.expand_frame_repr', False)


def get_company_information(symbol: str) -> pd.DataFrame:
    f_symbol = format_symbol_point_exchange(symbol)
    base_url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_BASIC_ORGINFO&columns=SECUCODE%2CSECURITY_CODE%2CSECURITY_NAME_ABBR%2CORG_CODE%2CORG_NAME%2CORG_NAME_EN%2CFORMERNAME%2CSTR_CODEA%2CSTR_NAMEA%2CSTR_CODEB%2CSTR_NAMEB%2CSTR_CODEH%2CSTR_NAMEH%2CSECURITY_TYPE%2CEM2016%2CTRADE_MARKET%2CINDUSTRYCSRC1%2CPRESIDENT%2CLEGAL_PERSON%2CSECRETARY%2CCHAIRMAN%2CSECPRESENT%2CINDEDIRECTORS%2CORG_TEL%2CORG_EMAIL%2CORG_FAX%2CORG_WEB%2CADDRESS%2CREG_ADDRESS%2CPROVINCE%2CADDRESS_POSTCODE%2CREG_CAPITAL%2CREG_NUM%2CEMP_NUM%2CTATOLNUMBER%2CLAW_FIRM%2CACCOUNTFIRM_NAME%2CORG_PROFILE%2CBUSINESS_SCOPE%2CTRADE_MARKETT%2CTRADE_MARKET_CODE%2CSECURITY_TYPEE%2CSECURITY_TYPE_CODE%2CEXPAND_NAME_ABBR%2CEXPAND_NAME_PINYIN&quoteColumns=&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize=1&sortTypes=&sortColumns=&source=HSF10&client=PC'
    url = base_url.format(f_symbol)
    # 获取网络数据
    data = get_web_json_content(url)['result']['data']
    df = pd.DataFrame(data)
    df.rename(columns={'SECURITY_CODE': 'symbol', 'SECURITY_NAME_ABBR': 'name', 'PROVINCE': 'province'}, inplace=True)
    df.drop(columns=['SECUCODE', 'ORG_CODE'], inplace=True)
    return df


def get_companies_information(symbols: Union[str, List[str]]) -> pd.DataFrame:
    if isinstance(symbols, str):
        symbols = [symbols]

    df = concat_dfs(func=get_company_information, datas=symbols)
    return df




def save_all_companies_information():
    print('更新【公司概况】--【基本资料】【东方财富】...')

    symbols = get_all_symbols()
    df = get_companies_information(symbols)

    # 添加更新日期数据
    from cnquant.data.trading_day import data_update_date
    df['update_date'] = data_update_date()

    df.to_csv(get_file_path_companies_information(), index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    save_all_companies_information()
