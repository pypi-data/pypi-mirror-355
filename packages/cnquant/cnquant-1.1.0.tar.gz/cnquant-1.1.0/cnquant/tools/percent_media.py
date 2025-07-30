"""
计算今天的涨跌幅的中位数
"""


def get_today_percent_media():
    # 计算今日涨跌幅中位数
    from cnquant.data.symbol.get_symbols import get_all_symbols
    from cnquant.data.market_data import get_market_data_em

    symbols = get_all_symbols()
    df = get_market_data_em(symbols)

    percent_median = df['percent'].median()  # 涨跌幅中位数
    print(f'今天的涨跌幅中位数是：{percent_median}%')

    return percent_median


if __name__ == '__main__':
    get_today_percent_media()