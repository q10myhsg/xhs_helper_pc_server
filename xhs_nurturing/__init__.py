"""小红书养号自动化包"""

__version__ = "1.0.0"

import logging

# 配置统一的日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
)

from .device_manager import DeviceManager
from .config_manager import ConfigManager
from .interaction_manager import InteractionManager
from .browse_manager import BrowseManager
from .nurturing_manager import NurturingManager

from .utils import random_delay, get_screen_size

__all__ = [
    "DeviceManager",
    "ConfigManager",
    "InteractionManager",
    "BrowseManager",
    "NurturingManager",
    "random_delay",
    "get_screen_size"
]