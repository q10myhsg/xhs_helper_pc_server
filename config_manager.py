import json
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置文件管理类"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.ensure_config_exists()
    
    def ensure_config_exists(self):
        """确保配置文件存在"""
        os.makedirs(os.path. dirname(self.config_path), exist_ok=True)
        if not os.path.exists(self.config_path):
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json. dump({}, f, indent=2, ensure_ascii=False)
    
    def load_config(self) -> Dict:
        """读取整个配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return {}
    
    def save_config_file(self, data: Dict):
        """保存整个配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("配置文件已保存")
        except Exception as e: 
            logger.error(f"保存配置文件失败:  {e}")
    
    def get_config(self, device_id: str) -> Optional[Dict]:
        """获取指定设备的配置"""
        config = self.load_config()
        return config.get(device_id)
    
    def save_config(self, device_id: str, config: Dict):
        """保存指定设备的配置"""
        data = self.load_config()
        data[device_id] = config
        self.save_config_file(data)
    
    def get_default_template(self) -> Dict:
        """获取默认配置模板"""
        config = self.load_config()
        return config.get("_default", self._create_default_template())
    
    def set_default_template(self, template: Dict):
        """设置默认配置模板"""
        config = self.load_config()
        config["_default"] = template
        self.save_config_file(config)
    
    def _create_default_template(self) -> Dict:
        """创建默认模板"""
        return {
            "keywords": ["科技资讯", "旅行攻略", "美食教程"],
            "duration_minutes": 20,
            "post_visit_ratio": 50,
            "posts_per_keyword": 10,
            "discovery_browse_time": 10,
            "visit_control": {
                "filter_image_text": True,
                "duration_range": [25, 45],
                "slide_interval": [3, 5],
                "slide_distance":  "single_image"
            },
            "interaction": {
                "like_prob": 15,
                "collect_prob": 10,
                "comment_prob": 5,
                "comment_templates": [
                    "不错的分享！",
                    "学习了~",
                    "感谢分享"
                ]
            }
        }