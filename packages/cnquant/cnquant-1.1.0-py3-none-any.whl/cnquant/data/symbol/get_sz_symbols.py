"""
获取深证A股的股票代码，包括深证主板A股和创业版,不包括已经退市的股票
已经核对过，获取的数量都是正确的
"""
import time
import random
import pandas as pd
import requests
from tqdm.auto import tqdm

from cnquant.core.get_web_data import get_web_json_content


def get_sz_symbols(url) -> pd.DataFrame:
    """
    获取深证证券交易所股票代码及名称数据，没有行情数据
    """
    # 创建列表存储df数据
    dfs = []

    base_url = url + '&PAGENO=%s' + '&random=' + str(random.random())
    # 1.先获取多少页
    resp = get_web_json_content(url)
    page_count = resp[0]['metadata']['pagecount']
    # symbol_num = resp[0]['metadata']['recordcount']
    # print(symbol_num)

    # 2.循环获取股票列表
    for i in tqdm(range(1, page_count + 1)):
        _url = base_url % str(i)

        # 获取单页的数据内容
        _resp = get_web_json_content(_url)
        # 解析数据
        _data = _resp[0]['data']
        _df = pd.DataFrame(data=_data)

        _df['name'] = _df['agjc'].str.extract(r'<u>(.*?)</u>')
        _df = _df[['agdm', 'name']]
        _df.rename(columns={'agdm': 'symbol'}, inplace=True)

        # 合并数据
        dfs.append(_df)

        time.sleep(2 * random.random())  # 需要停一下，深证交易所会限制

    # 把dfs列表里面的数据concat在一起
    df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

    return df


# 深交所主板和创业版的股票代码列表
def get_sz_a_symbols() -> pd.DataFrame:
    """
    获取深证证券交易所：所有的A股股票代码及名称数据
    """
    # print('正在获取深证股票代码及名称数据...')
    #
    # url = 'https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1110&TABKEY=tab1'
    # df = get_sz_symbols(url)
    # return df

    # 直接获取容易报错，从excel里面直接下载速度快
    max_tries = 5
    for i in range(max_tries):
        try:
            df = get_sz_a_symbols_from_xlsx()
            return df
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)


# 深证主板A股股票代码列表
def get_sz_zb_symbols() -> pd.DataFrame:
    """
    获取深证证券交易所：主板A股股票代码及名称数据
    """
    url = 'https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1110&TABKEY=tab1&selectModule=main'
    df = get_sz_symbols(url)
    return df


# 创业版股票代码列表
def get_sz_cy_symbols():
    """
    获取深证证券交易所：创业板A股股票代码及名称数据
    """
    url = 'https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1110&TABKEY=tab1&selectModule=nm'

    kc_symbols = get_sz_symbols(url)
    return kc_symbols


# 深交所主板和创业板所有的股票代码列表，从excel文件读取
def get_sz_a_symbols_from_xlsx() -> pd.DataFrame:
    print('正在获取深证股票代码及名称数据...')

    url = 'http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1110&TABKEY=tab1&random=0.35413040961763786'

    resp = requests.get(url)

    if resp.status_code == 200:
        # 忽略特定的警告
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

        #  使用 BytesIO 读取二进制数据流，pandas 读取 Excel 内容
        from io import BytesIO
        data = BytesIO(resp.content)

        _df = pd.read_excel(data, dtype={'A股代码': str})

        # 取出需要的股票代码及名称数据
        df = _df[['A股代码', 'A股简称']]
        df.columns = ['symbol', 'name']
        return df
    else:
        print(f"深圳证券股票市场A股数据下载失败. 状态码: {resp.status_code}")


if __name__ == '__main__':
    b = get_sz_a_symbols()
    print(b)
    print(len(b))
    # get_sz_a_symbols_from_xlsx()
