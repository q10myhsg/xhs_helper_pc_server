"""
路径管理模块 - 提供统一的隐蔽存储位置
Windows 和 Mac 通用

存储策略：把配置目录放到 OS 系统隐藏路径中，
普通用户不会主动去翻这些位置：
  macOS  → ~/Library/Application Support/com.apple.updates/
  Windows → %LOCALAPPDATA%\Microsoft\EdgeData\
  Linux  → ~/.local/share/.sys_updates/
"""
import os
import sys
import shutil


def _get_legacy_config_dir():
    """返回旧版配置目录路径（用于迁移），不创建目录"""
    home = os.path.expanduser("~")
    for dir_name in (".app_storage", ".system_data", ".local_cache",
                     ".user_preferences", ".config_cache"):
        candidate = os.path.join(home, dir_name)
        if os.path.exists(candidate):
            return candidate
    return None


def get_app_config_dir() -> str:
    """
    获取主配置目录。
    - 首次运行：在 OS 系统隐藏路径下创建目录
    - 旧数据存在：自动迁移到新目录后删除旧目录
    """
    home = os.path.expanduser("~")

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
        config_dir = os.path.join(base, "Microsoft", "EdgeData")
    elif sys.platform == "darwin":
        config_dir = os.path.join(home, "Library", "Application Support", "com.apple.updates")
    else:
        config_dir = os.path.join(home, ".local", "share", ".sys_updates")

    os.makedirs(config_dir, exist_ok=True)

    # 迁移旧数据（静默处理，失败不影响启动）
    legacy = _get_legacy_config_dir()
    if legacy and legacy != config_dir:
        try:
            for filename in os.listdir(legacy):
                src = os.path.join(legacy, filename)
                dst = os.path.join(config_dir, filename)
                if not os.path.exists(dst):
                    shutil.move(src, dst)
            shutil.rmtree(legacy, ignore_errors=True)
        except Exception:
            pass

    return config_dir


CONFIG_DIR = get_app_config_dir()

CONFIG_JSON_PATH          = os.path.join(CONFIG_DIR, ".sys_cfg.json")
LICENSE_DB_PATH           = os.path.join(CONFIG_DIR, ".sys_cache.db")
API_CONFIG_PATH           = os.path.join(CONFIG_DIR, ".api_cfg.json")
PACKAGE_CONFIG_PATH       = os.path.join(CONFIG_DIR, ".pkg_cfg.json")
PACKAGE_FETCH_DATE_PATH   = os.path.join(CONFIG_DIR, ".fetch_date.json")
PDF_PATHS_CONFIG_FILE     = os.path.join(CONFIG_DIR, ".pdf_paths.json")
PDF_IMAGES_CONFIG_FILE    = os.path.join(CONFIG_DIR, ".pdf_images.json")
FILE_TRANSFER_CONFIG_FILE = os.path.join(CONFIG_DIR, ".file_transfer.json")
