import datetime
import time

from cnquant.config.data_columns.dividend_ths_cn_columns import dividend_ths_cn_columns
from cnquant.data.dividend.dividend_ths import get_companies_dividend_ths
from cnquant.utils.sendemail import send_email


def holds_dividend():
    target = False

    # 监控股票代码
    symbols = [
        '601939',  # 建设银行
        '600028',  # 中国石化
        '600900',  # 长江电力
        '601006',  # 大秦铁路
    ]

    # 获取最新分红数据
    df = get_companies_dividend_ths(symbols=symbols)

    # 提取最新分红的数据
    latest_df_group = df.groupby('symbol')
    data_df = latest_df_group.head(1).reset_index(drop=True)

    # 修改列名
    data_df.rename(columns=dividend_ths_cn_columns, inplace=True)

    # 取出今天除权除息的股票
    today = str(datetime.date.today())
    today_dividend_df = data_df[data_df['A股除权除息日'] == today]

    # 发送邮件df
    print(today_dividend_df)
    if len(today_dividend_df) > 0:
        mail = "33688114@qq.com"
        title = f"{today}：今天有分红的股票"
        # 发送邮件
        send_email(mail, title, content=today_dividend_df.to_string(index=False))
        target = True
    return target


if __name__ == '__main__':
    while True:
        target = holds_dividend()
        if target:  # 发送了邮件，延迟24小时
            time.sleep(60*60*24)
        else:  # 没有股票分红，等待1分钟后循环
            time.sleep(60)
