"""
获取上证A股的股票代码，包括上证主板A股和科创板,不包括已经退市的股票
"""
import pandas as pd

from cnquant.core.get_web_data import get_web_json_content


def get_sh_symbols(url: str) -> pd.DataFrame:
    """
    获取网络数据，提取股票代码及股票名称。其实还有价格，涨跌幅等其他数据，速度快
    """
    resp = get_web_json_content(url=url)
    data = resp['list']
    df = pd.DataFrame(data=data)
    df = df[[0, 1]]  # 返回股票代码和股票名称
    df.rename(columns={0: 'symbol', 1: 'name'}, inplace=True)

    return df


# 上证主板A股股票代码列表
def get_sh_zb_symbols() -> pd.DataFrame:
    url = 'http://yunhq.sse.com.cn:32041/v1/sh1/list/exchange/ashare?select=code,name,open,high,low,last,prev_close,chg_rate,volume,amount,tradephase,change,amp_rate,cpxxsubtype,cpxxprodusta&order=&begin=0&end=25000'
    df = get_sh_symbols(url)
    return df


# 科创版股票代码列表
def get_sh_kc_symbols() -> pd.DataFrame:
    url = 'http://yunhq.sse.com.cn:32041/v1/sh1/list/exchange/kshare?select=code,name,open,high,low,last,prev_close,chg_rate,volume,amount,tradephase,change,amp_rate,cpxxsubtype,cpxxprodusta&order=&begin=0&end=25000'

    df = get_sh_symbols(url)
    return df


def get_sh_a_symbols():
    print('正在获取上证股票代码及名称数据...')

    df1 = get_sh_zb_symbols()
    df2 = get_sh_kc_symbols()
    return pd.concat([df1, df2], ignore_index=True)


if __name__ == '__main__':
    a = get_sh_a_symbols()
    print(a)
    print(len(a))

