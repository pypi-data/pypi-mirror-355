import json
import random
import time

import requests
from retry import retry
from cnquant.core.api import get_post_json_content
from cnquant.utils.logger import logger
from cnquant.config.config import LOGGER_SHOW
import jionlp

"""
字段：
省：province
市：city
区/县：district


### 快递公司
韵达快递：http://membernew.yundasys.com:15116/member.website/hywz/view/shipping.html
申通快递：https://www.sto.cn/pc/service-page/iframe_1_11
中通快递：https://my.zto.com/create
极兔快递：
快递100：

## 要登录
顺丰速运
圆通快递
EMS
德邦快递
"""


def parse_address_from_jionlp(address):
    data = jionlp.parse_location(address)
    return data['city'], data['county']


def parse_address_from_yt(address):
    """
    没有数量限制，地址长度有限制[100个字符]
    :param address:
    :return:
    """
    address = address[:100]

    if '\u4e00' <= address[0] <= '\u9fff':
        url = 'https://www.yto.net.cn/ec/order/smartEntering'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
        }
        data = {"address": address}
        data = json.dumps(data)
        resp = get_post_json_content(url=url, headers=headers, data=data)
        address = resp.get('data')
        return address['city'], address['county']
    else:
        print(f"{address}：此地址不是国内地址，无法解析")
        return None, None


def parse_address_from_zto(address):
    """
    # 中通快递
    """
    url = 'https://hdgateway.zto.com/Word_AnalysisAddress'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    data = {
        'address': address
    }

    resp = requests.post(url, headers=headers, json=data)
    data = json.loads(resp.text)
    address = data['result']['items'][0]
    return address['city'], address['district']


def parse_address_from_yd(address):
    url = 'http://membernew.yundasys.com:15116/ydaddress/AddrAnalysis'  # 韵达
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': 'http://membernew.yundasys.com:15116/member.website/hywz/view/shipping.html',
        'Cookie': 'cna=d116587956fe49729e1293961c2d52d1; sceneId=8f398514d6734c7395c7b221acfe2178'
    }
    params = {
        'appid': 'ydmb',
        'isSave': 'N',
        'openid': 'undefined',
        'receiverInfo': address,
        'req_time': int(time.time() * 1000),
        'version': 'V1.0',
    }

    resp = requests.post(url, headers=headers, data=json.dumps(params))
    data = json.loads(resp.text)
    # address = data['result']['items'][0]
    return data


def parse_address_from_sto(address):
    url = 'https://site.sto.cn/Service/IntelligentAddressResolution'  # 申通
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    data = {
        'Content': address
    }

    resp = requests.post(url, headers=headers, data=data)
    print(resp.text)


def parse_address_from_kd100(address: str):
    """
    快递100，单日不超过100个
    :param address:
    :return:
    """
    if not address[0].isalpha():
        url = 'https://www.kuaidi100.com/market/open/sent.do'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        data = {
            'method': 'infosplit',
            'content': address,
        }

        data = get_post_json_content(url=url, headers=headers, data=data)
        _address = data['data'][0]['xzq']['indexFullName']
        # 解析数据
        _address['city'] = _address.pop('secondName')
        _address['district'] = _address.pop('thirdName')
        del _address['firstName']

        return _address
    else:
        print(f"{address}此地址不是国内地址，无法解析")


def parse_address_from_sf(address):
    """
    顺丰，很多无法解析出来
    :param address:
    :return:
    """
    print(address)
    if '\u4e00' <= address[0] <= '\u9fff':
        url = 'https://www.sf-express.com/sf-service-core-web/service/nlp/address/mainlandChina/resolve?lang=sc&region=cn&translate=sc'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
        }
        data = {'address': address}
        data = json.dumps(data)

        resp = get_post_json_content(url=url, headers=headers, data=data)
        address = resp['result'][0]
        return address['city'], address['district']

    else:
        print(f"{address}：此地址不是国内地址，无法解析")
        return None, None


def parse_address(address, try_num=5):

    # 从jionlp获取数据
    data = parse_address_from_jionlp(address)

    # 如果数据是空的，从圆通接口里面获取
    if any(item is None for item in data):  # 如果结果里面有None
        for i in range(try_num):
            try:
                data = parse_address_from_yt(address)
                break
            except Exception as e:
                print(f'第{i+1}次重试，{e}')
                time.sleep(random.random())

    # 如果数据还是不行，从中通获取
    if any(data):  # 如果里面有空值，则再去中通里面获取一下
        for i in range(try_num):
            try:
                data = parse_address_from_zto(address)
                break
            except Exception as e:
                print(f'第{i+1}次重试，{e}')
                time.sleep(random.random())

    return data


if __name__ == '__main__':
    s = '宁夏回族自治区中卫市'
    # s = '江苏扬子江国际化工园北京路20号'
    # s = '浙江省杭州湾上虞经济技术开发区东一区至远路2号'
    # s = '广州市广州高新技术产业开发区科学城科丰路33号'
    # s = '哈尔滨高新技术产业开发区迎宾路集中区太湖北路7号'
    # s = '94 Solaris Avenue, Camana Bay, Grand Cayman, C...'
    # s = '浙江省湖州市东门十五里牌(318国道旁)'
    # a = parse_address_from_yt(s)
    # a = parse_address_from_zto(s)

    a = parse_address(s)
    #
    print(a)
