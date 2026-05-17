import json
import os
import logging
import sys
from typing import Dict, Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import DBManager

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化配置管理器
        :param config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.db_manager = DBManager()
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """
        确保配置文件目录存在
        """
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
            self.logger.info(f"创建配置文件目录: {config_dir}")
    
    def load_config(self) -> Dict:
        """
        加载配置文件
        :return: 配置字典
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_path}")
                return config
            else:
                self.logger.warning(f"配置文件不存在: {self.config_path}")
                return {}
        except json.JSONDecodeError:
            self.logger.error(f"配置文件格式错误: {self.config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def save_config(self, config: Dict):
        """
        保存配置文件
        :param config: 配置字典
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.logger.info(f"成功保存配置文件: {self.config_path}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def get_default_template(self) -> Dict:
        """
        获取默认配置模板
        :return: 默认配置模板
        """
        config = self.load_config()
        if "_default" in config:
            self.logger.info("使用配置文件中的默认模板")
            return config["_default"]
        else:
            self.logger.warning("配置文件中无默认模板，使用内置默认配置")
            return self._create_default_template()
    
    def set_default_template(self, template: Dict):
        """
        设置默认配置模板
        :param template: 默认配置模板
        """
        config = self.load_config()
        config["_default"] = template
        self.save_config(config)
        self.logger.info("已更新默认配置模板")
    
    def get_device_config(self, device_id: str) -> Dict:
        """
        获取设备配置
        :param device_id: 设备ID
        :return: 设备配置
        """
        config = self.load_config()
        if device_id in config:
            self.logger.info(f"使用设备 {device_id} 的配置")
            return config[device_id]
        else:
            self.logger.info(f"设备 {device_id} 无配置，使用默认模板")
            return self.get_default_template()
    
    def set_device_config(self, device_id: str, device_config: Dict):
        """
        设置设备配置
        :param device_id: 设备ID
        :param device_config: 设备配置
        """
        config = self.load_config()
        config[device_id] = device_config
        self.save_config(config)
        self.logger.info(f"已更新设备 {device_id} 的配置")
    
    def remove_device_config(self, device_id: str):
        """
        移除设备配置
        :param device_id: 设备ID
        """
        try:
            config = self.load_config()
            if device_id in config:
                del config[device_id]
                self.save_config(config)
                self.logger.info(f"已删除设备 {device_id} 的配置")
        except Exception as e:
            self.logger.error(f"移除设备配置失败: {e}")
            raise
    
    def remove_device_config(self, device_id: str):
        """
        移除设备配置
        :param device_id: 设备ID
        """
        try:
            config = self.load_config()
            if device_id in config:
                del config[device_id]
                self.save_config(config)
                self.logger.info(f"已删除设备 {device_id} 的配置")
        except Exception as e:
            self.logger.error(f"移除设备配置失败: {e}")
            raise
    
    def get_keywords(self, device_id: str) -> list:
        """
        获取设备关键词列表
        :param device_id: 设备ID
        :return: 关键词列表
        """
        keywords = self.db_manager.get_keywords(device_id)
        if keywords:
            return keywords
        
        config = self.get_device_config(device_id)
        return config.get("keywords", [])
    
    def set_keywords(self, device_id: str, keywords: list):
        """
        设置设备关键词列表
        :param device_id: 设备ID
        :param keywords: 关键词列表
        """
        self.db_manager.save_keywords(device_id, keywords)
        self.logger.info(f"已更新设备 {device_id} 的关键词列表")
    
    def get_comment_templates(self, device_id: str) -> list:
        """
        获取设备评论模板列表
        :param device_id: 设备ID
        :return: 评论模板列表
        """
        config = self.get_device_config(device_id)
        return config.get("interaction", {}).get("comment_templates", [])
    
    def set_comment_templates(self, device_id: str, comment_templates: list):
        """
        设置设备评论模板列表
        :param device_id: 设备ID
        :param comment_templates: 评论模板列表
        """
        device_config = self.get_device_config(device_id)
        if "interaction" not in device_config:
            device_config["interaction"] = {}
        device_config["interaction"]["comment_templates"] = comment_templates
        self.set_device_config(device_id, device_config)
        self.logger.info(f"已更新设备 {device_id} 的评论模板列表")
    
    def _create_default_template(self) -> Dict:
        """
        创建默认配置模板
        :return: 默认配置模板
        """
        return {
            "keywords": ["科技资讯", "旅行攻略", "美食教程"],
            "duration_minutes": 20,
            "post_visit_ratio": 50,
            "posts_per_keyword": 10,
            "discovery_browse_time": 10,
            "visit_control": {
                "duration_range": [25, 45],
                "slide_interval": [3, 5]
            },
            "interaction": {
                "like_prob": 15,
                "collect_prob": 10,
                "comment_prob": 5,
                "comment_templates": [
                    "不错的分享！",
                    "学习了~",
                    "感谢分享",
                    "很有用的内容",
                    "已收藏学习"
                ]
            },
            "browse": {
                "scroll_interval": 3,
                "note_read_time": 30,
                "max_notes_to_open": 10
            },
            "post": {
                "browse_time_before_post": 60,
                "browse_time_after_post": 60,
                "content": "你好中国",
                "image_count": 1,
                "location": "小学",
                "is_original": True,
                "tags": ["小学教辅"]
            }
        }
    
    def validate_config(self, config: Dict) -> bool:
        """
        验证配置有效性
        :param config: 配置字典
        :return: 是否有效
        """
        try:
            # 检查必要字段（keywords现在在数据库中，不检查）
            required_fields = ["duration_minutes", "post_visit_ratio", "posts_per_keyword", "discovery_browse_time"]
            for field in required_fields:
                if field not in config:
                    self.logger.warning(f"配置缺少必要字段: {field}")
                    return False
            
            # 检查数值范围
            if config["duration_minutes"] <= 0:
                self.logger.warning("养号时长必须大于0")
                return False
            
            if not 0 <= config["post_visit_ratio"] <= 100:
                self.logger.warning("帖子访问比例必须在0-100之间")
                return False
            
            if config["posts_per_keyword"] <= 0:
                self.logger.warning("每个关键词访问帖子数必须大于0")
                return False
            
            if config["discovery_browse_time"] <= 0:
                self.logger.warning("发现页浏览时间必须大于0")
                return False
            
            self.logger.info("配置验证通过")
            return True
        except Exception as e:
            self.logger.error(f"验证配置失败: {e}")
            return False