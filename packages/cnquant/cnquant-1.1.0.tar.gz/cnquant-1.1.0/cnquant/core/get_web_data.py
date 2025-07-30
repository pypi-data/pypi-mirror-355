import requests
import time
import json


def get_web_content(url, max_try_num=5):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62'}
    # 失败重试
    for i in range(max_try_num):
        try:
            resp = requests.get(url=url, headers=headers)
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)

    if resp.status_code == 200:
        return resp
    else:
        print('可能网络连接失败，程序退出')


def get_web_json_content(url, max_try_num=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Cookie': 'device_id=10f1012586ad13e92d7155c7503f6ee6; s=cw12g7z0sr; bid=e7ece59b09ddf25214cd537abd8febb5_kxd12dnh; __utmz=1.1639904951.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); Hm_lvt_1db88642e346389874251b5a1eded6e3=1640095857,1640096072; xq_a_token=8773bd0f088628c0bdb81c3a074786822710a682; xqat=8773bd0f088628c0bdb81c3a074786822710a682; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjQyMjkzOTQ2NzcsImlzcyI6InVjIiwiZXhwIjoxNjQyNDk2OTQzLCJjdG0iOjE2NDAwOTYxMDczODksImNpZCI6ImQ5ZDBuNEFadXAifQ.iBlrRK8Magh7H3Tnh-N8gXygXQcv_y7IRBOiYsK-wDKF7g4BtMaHNfZzhjj4THw4xLtOp16rowW0mvFg26FxoAZ2L5CRi7sEUvFUgw9OVSdrflE8flUcbe5X7UxTOeXAWuWG4jFj8tmRVZ10sBmx01dSN9KwgpOQfVctjbdLIAMAZkV-f_6iL-F1kx9V8_p2LxJGQhPkJjkfsMFn3QO-OKwRKV1nr4HdmBw2gcjQBRB7Od9SPy3oU1lbqqqDQ4mSQuHeZrRFo_a6QLjfexfGHAVBnHWKUa7zpB6gbO2voNPjtTVmI9cq53vegtnta4J9GUoGTDX8taxydMVIG3lSpA; xq_r_token=b50e0e9027d2080c13cb4881f8e23901d9a82254; xq_is_login=1; u=4229394677; __utmc=1; acw_tc=2760825f16400997284078275ec2efad7e9d779d31c46e9334f0c8cfeb4fda; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1640100049; __utma=1.388770240.1639904951.1640096117.1640100050.4; __utmt=1; __utmb=1.1.10.1640100050',
    }

    for i in range(max_try_num):
        try:
            resp = requests.get(url=url, headers=headers).text
            data = json.loads(resp)
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)

    if data is not None:
        return data
    else:
        print('可能网络连接失败，程序退出')


def get_web_json_content_xq(url, max_try_num=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Cookie': 'device_id=10f1012586ad13e92d7155c7503f6ee6; s=cw12g7z0sr; bid=e7ece59b09ddf25214cd537abd8febb5_kxd12dnh; __utmz=1.1639904951.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); Hm_lvt_1db88642e346389874251b5a1eded6e3=1640095857,1640096072; xq_a_token=8773bd0f088628c0bdb81c3a074786822710a682; xqat=8773bd0f088628c0bdb81c3a074786822710a682; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjQyMjkzOTQ2NzcsImlzcyI6InVjIiwiZXhwIjoxNjQyNDk2OTQzLCJjdG0iOjE2NDAwOTYxMDczODksImNpZCI6ImQ5ZDBuNEFadXAifQ.iBlrRK8Magh7H3Tnh-N8gXygXQcv_y7IRBOiYsK-wDKF7g4BtMaHNfZzhjj4THw4xLtOp16rowW0mvFg26FxoAZ2L5CRi7sEUvFUgw9OVSdrflE8flUcbe5X7UxTOeXAWuWG4jFj8tmRVZ10sBmx01dSN9KwgpOQfVctjbdLIAMAZkV-f_6iL-F1kx9V8_p2LxJGQhPkJjkfsMFn3QO-OKwRKV1nr4HdmBw2gcjQBRB7Od9SPy3oU1lbqqqDQ4mSQuHeZrRFo_a6QLjfexfGHAVBnHWKUa7zpB6gbO2voNPjtTVmI9cq53vegtnta4J9GUoGTDX8taxydMVIG3lSpA; xq_r_token=b50e0e9027d2080c13cb4881f8e23901d9a82254; xq_is_login=1; u=4229394677; __utmc=1; acw_tc=2760825f16400997284078275ec2efad7e9d779d31c46e9334f0c8cfeb4fda; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1640100049; __utma=1.388770240.1639904951.1640096117.1640100050.4; __utmt=1; __utmb=1.1.10.1640100050'}

    for i in range(max_try_num):
        try:
            resp = requests.get(url=url, headers=headers).text
            data = json.loads(resp)
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)

    if data is not None:
        return data
    else:
        print('可能网络连接失败，程序退出')


def get_post_content_bz(url, form_data, max_try_num=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Cookie': 'device_id=10f1012586ad13e92d7155c7503f6ee6; s=cw12g7z0sr; bid=e7ece59b09ddf25214cd537abd8febb5_kxd12dnh; __utmz=1.1639904951.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); Hm_lvt_1db88642e346389874251b5a1eded6e3=1640095857,1640096072; xq_a_token=8773bd0f088628c0bdb81c3a074786822710a682; xqat=8773bd0f088628c0bdb81c3a074786822710a682; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjQyMjkzOTQ2NzcsImlzcyI6InVjIiwiZXhwIjoxNjQyNDk2OTQzLCJjdG0iOjE2NDAwOTYxMDczODksImNpZCI6ImQ5ZDBuNEFadXAifQ.iBlrRK8Magh7H3Tnh-N8gXygXQcv_y7IRBOiYsK-wDKF7g4BtMaHNfZzhjj4THw4xLtOp16rowW0mvFg26FxoAZ2L5CRi7sEUvFUgw9OVSdrflE8flUcbe5X7UxTOeXAWuWG4jFj8tmRVZ10sBmx01dSN9KwgpOQfVctjbdLIAMAZkV-f_6iL-F1kx9V8_p2LxJGQhPkJjkfsMFn3QO-OKwRKV1nr4HdmBw2gcjQBRB7Od9SPy3oU1lbqqqDQ4mSQuHeZrRFo_a6QLjfexfGHAVBnHWKUa7zpB6gbO2voNPjtTVmI9cq53vegtnta4J9GUoGTDX8taxydMVIG3lSpA; xq_r_token=b50e0e9027d2080c13cb4881f8e23901d9a82254; xq_is_login=1; u=4229394677; __utmc=1; acw_tc=2760825f16400997284078275ec2efad7e9d779d31c46e9334f0c8cfeb4fda; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1640100049; __utma=1.388770240.1639904951.1640096117.1640100050.4; __utmt=1; __utmb=1.1.10.1640100050',
    }

    form_data = form_data

    for i in range(max_try_num):
        try:
            resp = requests.post(url=url, params=form_data, headers=headers).text
            data = json.loads(resp[5:-1])
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)

    if data is not None:
        return data
    else:
        print('可能网络连接失败，程序退出')


def get_post_json_content(url, headers, data, max_try_num=5):
    for i in range(max_try_num):
        try:
            resp = requests.post(url=url, headers=headers, data=data).text
            data = json.loads(resp)
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)

    if data is not None:
        return data
    else:
        print('可能网络连接失败，程序退出')


def get_klines_em(url, params, max_try_num=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    for i in range(max_try_num):
        try:
            resp = requests.get(url=url, params=params, headers=headers).text
            data = json.loads(resp)
            break
        except Exception as e:
            print(f'第{i + 1}次获取信息失败，5秒后重新尝试获取，{e}')
            time.sleep(5)

    if data is not None:
        return data
    else:
        print('可能网络连接失败，程序退出')
