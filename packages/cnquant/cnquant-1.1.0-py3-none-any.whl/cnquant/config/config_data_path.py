from pathlib import Path
from cnquant.config import get_data_dir, get_config_dir, get_temp_dir


def _ensure_parent_dir(file_path: Path) -> Path:
    """辅助函数，确保父目录存在并返回路径"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def _ensure_dir_exists(dir_path: Path) -> Path:
    """确保一个目录本身存在，并返回目录路径本身。"""
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


# --- Config Files (使用 get_config_dir) ---
def get_file_path_mail() -> Path:
    return _ensure_parent_dir(get_config_dir() / 'mail.json')


def get_file_path_db_conn() -> Path:
    return _ensure_parent_dir(get_config_dir() / 'mysql_db_conn.json')


# --- Temp Directory (使用 get_temp_dir) ---
def get_file_path_temp_dir() -> Path:
    path = get_temp_dir()
    path.mkdir(parents=True, exist_ok=True) # 确保目录存在
    return path


# --- Blacklist (黑名单属于用户配置, 也放入 config 目录) ---
def get_file_path_stock_blacklist() -> Path:
    return _ensure_parent_dir(get_config_dir() / 'stock_blacklist.csv')


# --- 以下所有核心数据文件，仍然使用 get_data_dir() ---
# **************************************开始**********************************
# base_data_dir
def get_file_path_trading_day_dir() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'trading_day')


# 实际控制人数据
def get_file_path_actual_controller() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'actual_controller.csv')


# 股票代码及名称
def get_file_path_symbols_names() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'symbols_names.csv')


# 公司信息
def get_file_path_companies_information() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'companies_information.csv')


# 公司省、市、区县
def get_file_path_companies_location() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'companies_location.csv')


# ipo信息
def get_file_path_ipos_information() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'ipos_information.csv')


# 申万行业
def get_file_path_sw_industry_classification() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'sw_industry_classification.csv')


# 股票历史名称
def get_file_path_history_name() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'base_data' / 'history_name.csv')
# ****************************************结束*****************************


# *************************************开始**********************************
# 股票分红信息
# 东方财富
def get_file_path_dividend_em() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'dividend' / 'dividend_em.csv')


# 同花顺
def get_file_path_dividend_ths() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'dividend' / 'dividend_ths.csv')


# *********************************************开始********************************
# 股东数据
# 股东数量数据
def get_file_path_holder_num() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'holder' / 'holder_num_em.csv')


# 十大股东
def get_file_path_holder() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'holder' / 'holder_em.csv')


# 十大流通股东
def get_file_path_free_holder() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'holder' / 'free_holder_em.csv')


# 最新日期的十大股东数据
def get_file_path_latest_holder() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'holder' / 'latest_holder_em.csv')


# 最新日期的十大流通股东数据
def get_file_path_latest_free_holder() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'holder' / 'latest_free_holder_em.csv')
# ******************************结束******************************


# ***************************开始******************************
# 财务数据
# 财务主要指标
def get_file_path_finance_main_index() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'finance' / 'finance_main_index.csv')


# 现金流表
def get_file_path_finance_cash_flow() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'finance' / 'cash_flow.csv')
# *****************************结束*******************************


# **************************************开始*****************************
# 经营分析
# 营业范围【东方财富】
def get_file_path_business_scope() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'business' / 'business_scope.csv')


# 主营业务分析【东方财富】
def get_file_path_main_business_composition_analysis() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'business' / 'main_business_composition_analysis.csv')


# 主营业务【同花顺】
def get_file_path_main_business_ths() -> Path:
    return _ensure_parent_dir(get_data_dir() / 'business' / 'main_business_ths.csv')
# *************************************结束*************************************


# *******************klines*************************
# klines数据
def get_file_path_klines_dir() -> Path:
    return _ensure_dir_exists(get_data_dir() / 'klines')


# index_klines
def get_file_path_index_klines_dir() -> Path:
    return _ensure_dir_exists(get_file_path_klines_dir() / 'index_klines')


# stock_klines
def get_file_path_stock_kines_dir() -> Path:
    return _ensure_dir_exists(get_file_path_klines_dir() / 'stock_klines')
# **********************************结束***********************
