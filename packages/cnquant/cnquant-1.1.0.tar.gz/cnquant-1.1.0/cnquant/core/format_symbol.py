def stock_exchange(symbol):
    if symbol.startswith('6'):
        exchange = 'SH'
    elif symbol.startswith('3') or symbol.startswith('0'):
        exchange = 'SZ'
    elif symbol.startswith('4') or symbol.startswith('8') or symbol.startswith('9'):
        exchange = 'BJ'
    return exchange


def format_exchange_symbol(symbol):
    """
    格式化股票代码
    SH600519
    SZ000002
    BJ831278
    """
    exchange = stock_exchange(symbol)
    if exchange == 'SH':
        symbol = 'SH' + symbol
    elif exchange == 'SZ':
        symbol = 'SZ' + symbol
    elif exchange == 'BJ':
        symbol = 'BJ' + symbol
    return symbol


def format_lower_exchange_symbol(symbol):
    """
    格式化股票代码
    SH600519
    SZ000002
    BJ831278
    """
    exchange = stock_exchange(symbol)
    if exchange == 'SH':
        symbol = 'sh' + symbol
    elif exchange == 'SZ':
        symbol = 'sz' + symbol
    elif exchange == 'BJ':
        symbol = 'bj' + symbol
    return symbol


def format_number_point_symbol(symbol):
    """
    格式化股票代码
    0.831278
    1.605178
    0.002699
    """
    exchange = stock_exchange(symbol)
    if exchange == 'SH':
        symbol = '1.' + symbol
    elif exchange == 'SZ':
        symbol = '0.' + symbol
    elif exchange == 'BJ':
        symbol = '0.' + symbol
    return symbol


def format_symbol_point_exchange(symbol):
    """
    格式化股票代码
    600519.SH
    000002.SZ
    831278.BJ
    """
    exchange = stock_exchange(symbol)
    if exchange == 'SH':
        symbol = symbol + '.SH'
    elif exchange == 'SZ':
        symbol = symbol + '.SZ'
    elif exchange == 'BJ':
        symbol = symbol + '.BJ'

    return symbol

