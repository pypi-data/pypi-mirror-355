__version__ = '1.1.0'
__author__ = 'XiaoQi'

from cnquant.config import (
    set_data_path,
    set_config_path,
    set_temp_path
)
from cnquant.data.api import (
    BlackList,
    # 股票实时股价数据
    get_all_market_data_em,
    get_market_data_em,
    get_market_data_xq,
)
from cnquant.update_data import (
    update_data,
    multithread_update_data,
)

from cnquant.query.api import (
    # company.location
    query_location_companies,
    # company.sw_industry_classification
    query_sw_industry_classification_company,

    rank_companies_number,
    query_companies_number,
    holder_num_rank,
    query_stock_holders,
    query_holders_hold_stocks,
    get_holder_total_capital_rank,
    query_actual_controller_hold_stock,
)
from cnquant.utils.sendemail import send_email


"""
api接口
"""

__all__ = [
    'set_data_path',
    'set_config_path',
    'set_temp_path',
    
    'rank_companies_number',
    'query_companies_number',

    'update_data',
    'multithread_update_data',

    # data
    'get_all_market_data_em',
    'get_market_data_em',
    'get_market_data_xq',

    # query
    'get_holder_total_capital_rank',
    'query_holders_hold_stocks',
    'holder_num_rank',
    'query_stock_holders',
    'query_actual_controller_hold_stock',
    'query_location_companies',
    'query_sw_industry_classification_company',

    'send_email',
]
