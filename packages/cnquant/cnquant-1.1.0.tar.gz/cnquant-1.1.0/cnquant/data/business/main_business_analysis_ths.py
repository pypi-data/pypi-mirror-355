"""
从同花顺F10页面获取主营构成分析
数据结构乱，目前还没有搞定
"""
import pandas as pd

from cnquant.core.get_web_data import get_web_json_content


def get_main_business_analysis_timestamp(symbol):
    url = f'https://basic.10jqka.com.cn/basicapi/operate/index/v1/history_end_date/?code={symbol}&market=33&type=stock&analysisTypes=area,product,industry'
    data = get_web_json_content(url)['data']
    df = pd.DataFrame(data)
    timestamp_list = df['date'].tolist()

    return timestamp_list


def get_main_business_analysis(symbol, timestamp):

    """
    # 这数据结构也太乱了，搞不定
    表头名称：
    symbol ,name, timestamp, 一级业务名称，二级业务名称，营业收入，收入比例，营业成本，成本比例，主营利润，利润比例，毛利率
    """
    url = f'https://basic.10jqka.com.cn/basicapi/operate/index/v1/product_index_query/?code={symbol}&market=33&type=stock&account=1&timeField=date&analysisTypes=product,area,industry&sortIndex=income&currency=CNY&level=1&expands=product_introduction&locale=zh_CN&date={timestamp}'
    resp1 = get_web_json_content(url)['data'][0]

    df = pd.json_normalize(resp1,
                           record_path=[
                               'time_operate_index_item_list',
                               'product_index_item_list',
                               'index_analysis_list',
                           ],
                           meta=['analysis_type']
                           )
    print(df)

    # df = pd.json_normalize(data=resp,
    #
    #                        record_path=[
    #                            'time_operate_index_item_list',
    #                            'product_index_item_list',
    #                            'index_analysis_list',
    #                        ],
    #                        meta=[
    #                            'analysis_type',
    #                            ['time_operate_index_item_list', 'time'],
    #                            ['time_operate_index_item_list', 'product_index_item_list', 'product_name']
    #                        ]
    #
    #                        # record_path=['time_operate_index_item_list',
    #                        #              'product_index_item_list',
    #                        #              'index_analysis_list',
    #                        #              ],
    #                        # meta=['analysis_type',
    #                        #      ['time_operate_index_item_list', 'time'],
    #                        #      ['time_operate_index_item_list', 'product_index_item_list', 'product_name']]
    #                        # meta=['analysis_type',
    #                        #       ['time_operate_index_item_list', 'product_index_item_list', 'product_name'],
    #                        #       ],
    #                        # max_level=3,
    #                        )
    # print(df)


if __name__ == '__main__':
    symbol = '600188'
    a = get_main_business_analysis_timestamp(symbol)
    timestamp = a[0]

    get_main_business_analysis(symbol, timestamp)

