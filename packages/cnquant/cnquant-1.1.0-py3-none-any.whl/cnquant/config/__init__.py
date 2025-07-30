import os
import sys
import tempfile
from pathlib import Path

# --- 路径覆盖的全局变量 ---
_data_path_override = None
_config_path_override = None
_temp_path_override = None


def set_data_path(path: str):
    """设置 cnquant 核心数据存储的根目录。"""
    global _data_path_override
    _data_path_override = os.path.abspath(path)
    Path(_data_path_override).mkdir(parents=True, exist_ok=True)
    print(f"cnquant 数据目录已设置为: {_data_path_override}")


def set_config_path(path: str):
    """
    (高级) 设置 cnquant 配置文件(如mail.json)存储的根目录。

    Args:
        path (str): 您想要存储配置文件的路径。
    """
    global _config_path_override
    _config_path_override = os.path.abspath(path)
    Path(_config_path_override).mkdir(parents=True, exist_ok=True)
    print(f"cnquant 配置目录已设置为: {_config_path_override}")


def set_temp_path(path: str):
    """
    设置 cnquant 临时文件存储的根目录。
    """
    global _temp_path_override
    _temp_path_override = os.path.abspath(path)
    Path(_temp_path_override).mkdir(parents=True, exist_ok=True)
    print(f"cnquant 临时目录已设置为: {_temp_path_override}")


# --- 内部路径获取函数 ---
def get_data_dir() -> Path:
    """获取核心数据根目录。"""
    if _data_path_override:
        return Path(_data_path_override)
    # 默认路径: ~/cn_finance_data
    default_path = Path.home() / 'cn_finance_data'
    default_path.mkdir(parents=True, exist_ok=True)
    return default_path


def get_config_dir() -> Path:
    """获取配置文件根目录 (遵循操作系统规范)。"""
    if _config_path_override:
        return Path(_config_path_override)

    # Windows: %APPDATA%/cnquant
    if sys.platform == "win32":
        path = Path(os.getenv("APPDATA")) / "cnquant"
    # macOS: ~/Library/Application Support/cnquant
    elif sys.platform == "darwin":
        path = Path.home() / 'Library' / 'Application Support' / 'cnquant'
    # Linux: ~/.config/cnquant
    else:
        path = Path.home() / '.config' / 'cnquant'

    path.mkdir(parents=True, exist_ok=True)
    return path


def get_temp_dir() -> Path:
    """获取临时文件根目录。"""
    if _temp_path_override:
        return Path(_temp_path_override)
    # 使用系统标准的临时目录，并在其中创建 cnquant 子目录
    path = Path(tempfile.gettempdir()) / "cnquant"
    path.mkdir(parents=True, exist_ok=True)
    return path
