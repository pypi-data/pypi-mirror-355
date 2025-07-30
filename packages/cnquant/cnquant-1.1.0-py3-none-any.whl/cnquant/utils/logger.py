import logging
from pathlib import Path

from cnquant.config.config_data_path import get_config_dir

# 定义一个全局变量来存储 logger 实例，防止重复创建
_logger_instance = None

def get_logger():
    """
    获取并配置一个日志记录器实例。

    使用单例模式，确保整个程序中只有一个 logger 实例。
    日志文件将存储在配置目录下。

    Returns:
        logging.Logger: 配置好的 logger 对象。
    """
    global _logger_instance

    # 2. 如果 logger 实例已经存在，直接返回它
    if _logger_instance:
        return _logger_instance

    # 3. 如果是第一次调用，则创建并配置 logger

    # 创建记录器对象
    logger = logging.getLogger('cnquant')
    logger.setLevel(logging.INFO)  # 设置记录器的阈值
    # 防止日志消息传递给父级记录器，避免重复输出
    logger.propagate = False

    # 创建一个格式器对象
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - [%(pathname)s line:%(lineno)d] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # --- 控制台处理器 ---
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)  # 设置处理器的阈值
    sh.setFormatter(formatter)  # 为处理器添加格式化器

    # --- 文件处理器 (使用新的动态路径) ---
    # 4. 在这里动态获取配置目录，并创建日志文件路径
    log_file_path = get_config_dir() / 'cnquant.log'

    fh = logging.FileHandler(log_file_path, encoding='utf-8')
    fh.setLevel(logging.WARNING)  # 设置处理器的阈值
    fh.setFormatter(formatter)  # 为处理器添加格式化器

    # 把处理器添加到记录器对象里面
    logger.addHandler(sh)
    logger.addHandler(fh)

    # 5. 将创建好的实例存入全局变量，并返回
    _logger_instance = logger
    return _logger_instance


# 6. 为了方便使用，可以直接创建一个别名
logger = get_logger()
