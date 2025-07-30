"""
停牌了后东方财富的数据是-，雪球的正常。

"""
import json
import time
from typing import List, Union
import requests
import pandas as pd
from cnquant.config.config import USER_AGENT
from cnquant.core.api import format_exchange_symbol, get_web_json_content
from cnquant.core.format_symbol import format_lower_exchange_symbol
from cnquant.data.symbol.get_symbols import get_all_symbols_and_names

pd.set_option('display.unicode.east_asian_width', True)


def get_all_market_data_em(max_retry=5):
    """
    从东方财富获取所有的实时股票价格数据
    耗时0.3s左右
    """
    base_url = 'https://41.push2.eastmoney.com/api/qt/clist/get'

    params = {
        'pn': 1,
        'pz': 200000,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'dect': 1,
        'wbp2u': '|0|0|0|web',
        'fid': 'f3',
        'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048',
        'fields': 'f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23',
    }

    columns = {
        'f2': 'newest_price',
        'f3': 'percent',
        'f4': 'change',
        'f5': 'volume(手)',
        'f6': 'amount(元)',
        'f7': 'amplitude',
        'f8': 'turnover_rate',
        'f9': 'pe_ttm',
        'f10': 'volume_ratio',
        # 'f11': '',
        'f12': 'symbol',
        'f14': 'name',
        'f15': 'high',
        'f16': 'low',
        'f17': 'open',
        'f18': 'pre_close',
        'f20': 'market_capital',
        'f21': 'float_market_capital',
        'f23': 'pb',
    }

    for i in range(max_retry):
        try:
            resp = requests.get(base_url, params=params, headers={'User-Agent': USER_AGENT})
            data = json.loads(resp.text).get('data').get('diff')
            df = pd.DataFrame(data)
            df.rename(columns=columns, inplace=True)
            return df  # return执行了，就表示这个函数结束运行了
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取, {e}')
            if i + 1 == max_retry:  # 达到最大尝试次数，返回空值
                return None
            time.sleep(5)


def get_market_data_em(symbols: Union[str, List[str]]) -> pd.DataFrame:
    """
    获取特定股票的价格数据
    """
    _df = get_all_market_data_em()

    if isinstance(symbols, str):
        symbols = [symbols]

    df = _df[_df['symbol'].isin(symbols)]

    # 格式化数据
    symbols_df = df.copy()
    # 暂停交易的percent是-，用0取代
    symbols_df.loc[(symbols_df['percent'] == '-'), 'percent'] = 0
    # 转为float
    symbols_df['percent'] = symbols_df['percent'].astype(float)

    symbols_df.reset_index(drop=True, inplace=True)
    return symbols_df


def get_market_data_xq(symbols: Union[str, List[str]]) -> pd.DataFrame:
    """
    雪球获取实时股票数据
    symbols: [SZ000001,SH600519]。如果不是，需要格式化：symbols = [format_exchange_symbol(symbol) for symbol in symbols]
    可以用来监控自选股
    也是0.3s左右，但是股票数量多了，还是的利用东方财富的，这个超过449个得循环查询了，耗时多
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    # 格式化股票代码
    f_symbols = [format_exchange_symbol(symbol) for symbol in symbols]

    # 读取股票名称数据，雪球的数据没有名称
    symbols_and_names = get_all_symbols_and_names()

    # 删除不必要的数据[名称更新日期]
    symbols_and_names.drop(columns=['update_date'], inplace=True)

    if len(f_symbols) > 449:
        # 雪球最大一次可以请求449个。分割一下股票代码列表
        symbols_size = 449
        chunks = [f_symbols[i:i + symbols_size] for i in range(0, len(f_symbols), symbols_size)]
        string_symbols = [','.join(map(str, chunk)) for chunk in chunks]
    else:
        string_symbols = [','.join(f_symbols)]

    _dfs = []
    # 循环获取数据
    for string_symbol in string_symbols:
        url = f'https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol={string_symbol}'
        data = get_web_json_content(url)['data']
        _df = pd.DataFrame(data)  # 停牌的股票数据有NaN

        # 处理一下空数据
        _df['amplitude'].fillna(value=0.0, inplace=True)  # 停牌股票振幅是0.0
        _df['open'].fillna(value=_df['last_close'], inplace=True)  # 开盘价跟昨天收盘价一样

        _dfs.append(_df)

    # 合并数据
    df = pd.concat([_df for _df in _dfs if not _df.empty], ignore_index=True)

    # 剔除不必要的数据
    df.drop(columns=['yield_to_maturity', 'trade_type_v2', 'traded_amount_ext', 'volume_ext', 'offer_appl_seq_num',
                     'bid_appl_seq_num', 'type', 'trade_unique_id', 'trade_type', 'trade_session', 'level', 'side',
                     'trade_volume'], inplace=True)
    # 整理数据
    df['symbol'] = df['symbol'].apply(lambda x: x[-6:])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    # 转为北京时间
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')
    # 取出日期
    # df['timestamp'] = df['timestamp'].dt.date

    # 合并名称数据
    new_df = pd.merge(df, symbols_and_names, on=['symbol'], how='left')
    """
    last_close: 昨收，current：现价，amplitude：振幅，avg_price：均价
    """

    # 把最后一列移动到第二列的位置
    new_df.insert(1, new_df.columns[-1], new_df.pop(new_df.columns[-1]))

    return new_df


def get_live_price_from_tx(symbols, max_retry=5):
    """
    腾讯接口，暂未完成
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    # 格式化股票代码
    f_symbols = [format_lower_exchange_symbol(symbol) for symbol in symbols]

    # 格式化股票代码列表
    string_symbols = ','.join(f_symbols)

    url = 'https://qt.gtimg.cn/q=' + string_symbols

    for i in range(max_retry):
        try:
            resp = requests.get(url, headers={'User-Agent': USER_AGENT}).text
            print(resp)
            break
            # data = json.loads(resp.text).get('data').get('diff')
            # df = pd.DataFrame(data)
            # df.rename(columns=columns, inplace=True)
            # return df  # return执行了，就表示这个函数结束运行了
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取, {e}')
            if i + 1 == max_retry:  # 达到最大尝试次数，返回空值
                return None
            time.sleep(5)


def get_live_price(symbols, func=get_market_data_xq):
    price_df = func(symbols)
    return price_df


if __name__ == '__main__':
    start = time.time()

    # from cnquant.data.symbol.get_symbols import get_all_symbols_and_names, get_all_symbols
    # symbols = get_all_symbols()

    symbols = ['600519', '000002', '603958']
    a = get_market_data_xq(symbols)
    print(a)
    #
    # get_live_price_from_tx(symbols)

    print(time.time() - start)

