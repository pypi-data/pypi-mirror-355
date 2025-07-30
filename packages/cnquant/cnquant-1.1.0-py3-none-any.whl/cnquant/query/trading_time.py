import datetime
from cnquant.data.trading_day import is_trading_day


def is_trading_time(timestamp: datetime.datetime) -> bool:
    _date = timestamp.date()
    _time = timestamp.time()

    if is_trading_day(_date):
        print(f'{timestamp.date()}是交易日')
        if datetime.time(9, 30) <= _time <= datetime.time(11, 30):
            print(f'现在是上午开盘时间：{_time.strftime("%H:%M:%S")}')
            return True
        if datetime.time(13, 0) <= _time <= datetime.time(15, 0):
            print(f'现在是下午开盘时间：{_time.strftime("%H:%M:%S")}')
            return True
        else:
            print(f'{_time}是非交易时间')
            return False
    else:
        print(f'{timestamp.date()}是非交易日')
        return False


if __name__ == '__main__':
    print(is_trading_time(datetime.datetime(2024, 7, 29, 11, 30, 1)))
