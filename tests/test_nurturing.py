import unittest
import time
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch
from xhs_nurturing.nurturing_manager import NurturingManager
from xhs_nurturing.device_manager import DeviceManager
from xhs_nurturing.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestNurturingManager(unittest.TestCase):
    """
    测试养号管理器的核心功能
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        logger.info("开始测试养号核心功能")
        self.nurturing_manager = NurturingManager()
        self.device_id = "test_device_123"
        
        # 模拟设备管理器
        self.mock_device = Mock()
        self.mock_device.app_start = Mock(return_value=True)
        self.mock_device.app_wait = Mock(return_value=True)
        self.mock_device.press = Mock(return_value=None)
        self.mock_device.click = Mock(return_value=True)
        self.mock_device.swipe = Mock(return_value=True)
        self.mock_device.info = {"model": "Test Device"}
        
        # 模拟配置
        self.test_config = {
            "keywords": ["测试关键词1", "测试关键词2"],
            "duration_minutes": 1,
            "posts_per_keyword": 2,
            "discovery_browse_time": 30,
            "post_visit_ratio": 50,
            "max_posts_per_run": 10,
            "visit_control": {
                "filter_image_text": True,
                "duration_range": [25, 45],
                "slide_interval": [3, 5],
                "slide_distance": "single_image"
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
            }
        }
    
    def tearDown(self):
        """
        测试后的清理工作
        """
        logger.info("测试完成，清理资源")
        # 清理运行任务
        if self.device_id in self.nurturing_manager._running_tasks:
            self.nurturing_manager._running_tasks.remove(self.device_id)
    
    @patch('xhs_nurturing.device_manager.u2.connect')
    def test_start_nurturing(self, mock_connect):
        """
        测试启动养号功能
        """
        logger.info("测试启动养号功能")
        
        # 模拟设备连接
        mock_connect.return_value = self.mock_device
        
        # 模拟配置管理器
        with patch.object(ConfigManager, 'get_device_config', return_value=self.test_config):
            with patch.object(ConfigManager, 'validate_config', return_value=True):
                # 模拟设备管理器的方法
                with patch.object(DeviceManager, 'connect_device', return_value=True):
                    with patch.object(DeviceManager, 'get_device', return_value=self.mock_device):
                        with patch.object(DeviceManager, 'update_device_status', return_value=None):
                            with patch.object(DeviceManager, 'is_stop_requested', return_value=False):
                                # 测试启动养号
                                result = self.nurturing_manager.start_nurturing(self.device_id)
                                self.assertTrue(result, "启动养号应该成功")
                                
                                # 验证设备是否添加到运行任务
                                self.assertIn(self.device_id, self.nurturing_manager._running_tasks)
                                
                                # 等待一段时间让养号流程执行
                                logger.info("等待养号流程执行...")
                                time.sleep(5)
                                
                                # 停止养号
                                self.nurturing_manager.stop_nurturing(self.device_id)
                                logger.info("养号测试完成")
    
    def test_get_device_status(self):
        """
        测试获取设备状态
        """
        logger.info("测试获取设备状态")
        
        # 模拟设备管理器的方法
        with patch.object(DeviceManager, 'device_status', return_value={
            "is_running": False,
            "remain_time": 0,
            "visited": 0,
            "current_keyword": "",
            "connection_status": "offline"
        }):
            status = self.nurturing_manager.get_device_status(self.device_id)
            self.assertIsInstance(status, dict, "设备状态应该是字典类型")
            self.assertIn("is_running", status, "设备状态应该包含is_running字段")
            logger.info(f"设备状态: {status}")
    
    def test_update_keywords(self):
        """
        测试更新设备关键词
        """
        logger.info("测试更新设备关键词")
        
        test_keywords = ["新关键词1", "新关键词2", "新关键词3"]
        
        # 模拟配置管理器的方法
        with patch.object(ConfigManager, 'set_keywords', return_value=None):
            result = self.nurturing_manager.update_keywords(self.device_id, test_keywords)
            self.assertTrue(result, "更新关键词应该成功")
            logger.info(f"更新关键词成功: {test_keywords}")
    
    def test_is_device_running(self):
        """
        测试检查设备是否正在养号
        """
        logger.info("测试检查设备是否正在养号")
        
        # 初始状态：设备不在运行中
        is_running = self.nurturing_manager.is_device_running(self.device_id)
        self.assertFalse(is_running, "初始状态下设备应该不在运行中")
        
        # 添加到运行任务
        self.nurturing_manager._running_tasks.add(self.device_id)
        
        # 检查状态：设备正在运行中
        is_running = self.nurturing_manager.is_device_running(self.device_id)
        self.assertTrue(is_running, "添加到运行任务后设备应该正在运行中")
        
        # 从运行任务中移除
        self.nurturing_manager._running_tasks.remove(self.device_id)
        
        # 检查状态：设备不在运行中
        is_running = self.nurturing_manager.is_device_running(self.device_id)
        self.assertFalse(is_running, "从运行任务中移除后设备应该不在运行中")
        
        logger.info("测试检查设备运行状态完成")

if __name__ == '__main__':
    unittest.main()
