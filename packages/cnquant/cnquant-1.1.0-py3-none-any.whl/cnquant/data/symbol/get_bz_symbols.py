import random
import time
import pandas as pd
from tqdm.auto import tqdm
from cnquant.core.get_web_data import get_post_content_bz

"""
获取北京证券交易所股票代码和名称数据
"""


def get_bz_symbols() -> pd.DataFrame:
    """
    获取股票代码及名称数据。也有实时行情数据：价格，涨跌幅，成交量，成交额
    """
    url = 'https://www.bse.cn/nqhqController/nqhq_en.do'
    page = 0  # 第一页
    form_data = {
        'page': page,
        'type_en': '["B"]',
        'sortfield': 'hqcjsl',
        'sorttype': 'desc',
        'xxfcbj_en': '[2]',
        'zqdm': '',
    }

    # 数据获取
    resp = get_post_content_bz(url, form_data)
    data = resp[0]
    page_count = data['totalPages']

    print('正在获取北证股票代码及名称数据...')

    _df_list = []
    for _page in tqdm(range(page_count)):
        form_data['page'] = _page
        _resp = get_post_content_bz(url, form_data)
        _data = _resp[0]['content']
        _df = pd.DataFrame(data=_data)

        # 提取股票代码及股票名称数据
        _df = _df[['hqzqdm', 'hqzqjc']]

        # 合并数据
        _df_list.append(_df)
        time.sleep(2 * random.random())

    # 数据合并
    df = pd.concat([_df for _df in _df_list if not _df.empty], ignore_index=True)

    # 统一修改列名称
    df.rename(columns={'hqzqdm': 'symbol', 'hqzqjc': 'name'}, inplace=True)
    return df


if __name__ == '__main__':
    a = get_bz_symbols()
    print(a)
    print('一共%s条数据' % len(a))

