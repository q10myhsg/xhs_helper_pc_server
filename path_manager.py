"""
路径管理模块 - 提供统一的隐蔽存储位置
Windows 和 Mac 通用
"""
import os


def get_app_config_dir():
    """获取应用配置目录，Windows/Mac 通用"""
    home = os.path.expanduser("~")
    # 使用多个隐蔽的文件夹名备选
    hidden_dirs = [
        ".app_storage",
        ".system_data",
        ".local_cache",
        ".user_preferences",
        ".config_cache"
    ]
    # 检查是否有已存在的目录
    for dir_name in hidden_dirs:
        test_dir = os.path.join(home, dir_name)
        if os.path.exists(test_dir):
            return test_dir
    # 如果没有已存在的，使用第一个创建
    config_dir = os.path.join(home, hidden_dirs[0])
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


# 配置文件路径 - 使用隐蔽的存储位置
CONFIG_DIR = get_app_config_dir()

# 各个配置文件
CONFIG_JSON_PATH = os.path.join(CONFIG_DIR, ".sys_cfg.json")
LICENSE_DB_PATH = os.path.join(CONFIG_DIR, ".sys_cache.db")
API_CONFIG_PATH = os.path.join(CONFIG_DIR, ".api_cfg.json")
PACKAGE_CONFIG_PATH = os.path.join(CONFIG_DIR, ".pkg_cfg.json")
PACKAGE_FETCH_DATE_PATH = os.path.join(CONFIG_DIR, ".fetch_date.json")
PDF_PATHS_CONFIG_FILE = os.path.join(CONFIG_DIR, ".pdf_paths.json")
PDF_IMAGES_CONFIG_FILE = os.path.join(CONFIG_DIR, ".pdf_images.json")
FILE_TRANSFER_CONFIG_FILE = os.path.join(CONFIG_DIR, ".file_transfer.json")

