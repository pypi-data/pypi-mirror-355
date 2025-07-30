import json
import requests
import time

from cnquant.config.config import USER_AGENT


def get_web_data_em_hsf10(params, max_try_num=5):
    headers = {
        'User-Agent': USER_AGENT,
    }
    url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get'

    for i in range(max_try_num):
        try:
            resp = requests.get(url, headers=headers, params=params).text
            data = json.loads(resp)
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)
    if data is not None:
        return data
    else:
        print('可能网络连接失败，程序退出')
