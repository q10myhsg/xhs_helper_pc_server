import uiautomator2 as u2
import subprocess
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from .config_manager import ConfigManager

class DeviceManager:
    """设备管理器"""
    
    def __init__(self):
        """
        初始化设备管理器
        """
        self._devices_pool: Dict[str, u2.Device] = {}
        self._status: Dict[str, dict] = {}
        self._stop_flag: Dict[str, bool] = {}
        self._device_aliases: Dict[str, str] = {}  # 存储设备别名
        self.config_manager = ConfigManager()  # 配置管理器
        self.logger = logging.getLogger(__name__)
        # 从配置文件加载设备别名
        self._load_device_aliases()
    
    def get_devices(self) -> List[Dict]:
        """
        获取已连接的ADB设备列表
        :return: 设备列表，每个设备包含id、name和status
        """
        try:
            # 使用subprocess调用adb命令获取设备列表
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            self.logger.info(f"adb devices输出: {result.stdout}")
            lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
            
            device_list = []
            self.logger.info(f"设备行数: {len(lines)}")
            
            for line in lines:
                self.logger.info(f"处理设备行: {line}")
                if line.strip():
                    parts = line.split('\t')
                    self.logger.info(f"分割结果: {parts}")
                    if len(parts) >= 2:
                        device_id = parts[0]
                        status = parts[1]
                        self.logger.info(f"设备ID: {device_id}, 状态: {status}")
                        
                        # 尝试连接并获取设备信息
                        try:
                            self.logger.info(f"尝试连接设备: {device_id}")
                            d = u2.connect(device_id)
                            
                            info = None
                            # 尝试获取设备信息
                            try:
                                info = d.info
                            except u2.exceptions.UiAutomationNotConnectedError:
                                self.logger.info(f"设备 {device_id} 的 uiautomator2 未启动，尝试使用 adb 命令初始化...")
                                # 尝试使用 adb 命令初始化 uiautomator2
                                try:
                                    # 使用 uiautomator2 的 init 方法
                                    subprocess.run(['python3', '-m', 'uiautomator2', 'init', '--device', device_id], 
                                                 capture_output=True, text=True)
                                    # 等待一下
                                    time.sleep(3)
                                    info = d.info
                                except Exception as init_error:
                                    self.logger.warning(f"初始化 uiautomator2 失败（这是正常的，设备依然可用）: {init_error}")
                                    # 即使初始化失败，也继续处理，因为我们会用 adb 状态判断
                            
                            if info:
                                self.logger.info(f"设备信息: {info}")
                                # 检查是否有设备别名
                                alias = self.get_device_alias(device_id)
                                if alias:
                                    device_name = alias
                                else:
                                    device_name = f"{info.get('model', 'Unknown')}({device_id})"
                                device_list.append({
                                    "id": device_id,
                                    "name": device_name,
                                    "status": "online"
                                })
                            else:
                                # 即使没有 info，只要 adb 显示 device，我们也标记为在线
                                raise Exception("uiautomator2 连接失败")
                        except Exception as e:
                            self.logger.error(f"连接设备失败: {e}")
                            # 即使 uiautomator2 连接失败，只要 adb 显示 device 状态，我们也标记为在线
                            if status == 'device':
                                self.logger.info(f"设备 {device_id} 通过 adb 检测为在线，标记为 online")
                                alias = self.get_device_alias(device_id)
                                if alias:
                                    device_name = alias
                                else:
                                    device_name = device_id
                                device_list.append({
                                    "id": device_id,
                                    "name": device_name,
                                    "status": "online"
                                })
                            else:
                                # 检查是否有设备别名
                                alias = self.get_device_alias(device_id)
                                if alias:
                                    device_name = alias
                                else:
                                    device_name = device_id
                                device_list.append({
                                    "id": device_id,
                                    "name": device_name,
                                    "status": "offline"
                                })
            
            self.logger.info(f"最终设备列表: {device_list}")
            return device_list
        except Exception as e:
            self.logger.error(f"获取设备列表失败: {e}")
            return []
    
    def connect_device(self, device_id: str) -> bool:
        """
        连接指定设备
        :param device_id: 设备ID
        :return: 是否连接成功
        """
        try:
            if device_id in self._devices_pool:
                del self._devices_pool[device_id]
            
            d = u2.connect(device_id)
            
            # 检查 uiautomator2 是否连接，如果没有则尝试初始化
            try:
                d.info
            except u2.exceptions.UiAutomationNotConnectedError:
                self.logger.info(f"设备 {device_id} 的 uiautomator2 未启动，尝试使用 adb 命令初始化...")
                # 尝试使用 adb 命令初始化 uiautomator2
                try:
                    # 使用 uiautomator2 的 init 方法
                    subprocess.run(['python3', '-m', 'uiautomator2', 'init', '--device', device_id], 
                                 capture_output=True, text=True)
                    # 等待一下
                    time.sleep(3)
                    d.info
                except Exception as init_error:
                    self.logger.warning(f"初始化 uiautomator2 失败（这是正常的，设备依然可用）: {init_error}")
            
            self._devices_pool[device_id] = d
            self._status[device_id] = {
                "is_running": False,
                "remain_time": 0,
                "visited": 0,
                "current_keyword": "",
                "connection_status": "online",
                "last_connected": datetime.now().isoformat()
            }
            self._stop_flag[device_id] = False
            self.logger.info(f"已连接设备: {device_id}")
            return True
        except Exception as e:
            self.logger.error(f"连接设备失败: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[u2.Device]:
        """
        获取设备连接
        :param device_id: 设备ID
        :return: 设备连接实例，若未连接返回None
        """
        return self._devices_pool.get(device_id)
    
    def is_device_online(self, device_id: str) -> bool:
        """
        检查设备是否在线
        :param device_id: 设备ID
        :return: 设备是否在线
        """
        device = self._devices_pool.get(device_id)
        if not device:
            return False
        try:
            # 尝试获取设备信息，如果成功则设备在线
            device.info
            return True
        except Exception as e:
            self.logger.error(f"检查设备在线状态失败: {e}")
            # 设备离线，从设备池中移除
            if device_id in self._devices_pool:
                del self._devices_pool[device_id]
            # 更新设备状态为离线
            self.update_device_status(device_id, is_running=False, remain_time=0, current_keyword="")
            return False
    
    def device_status(self, device_id: str) -> dict:
        """
        获取设备状态
        :param device_id: 设备ID
        :return: 设备状态
        """
        return self._status.get(device_id, {
            "is_running": False,
            "remain_time": 0,
            "visited": 0,
            "connection_status": "offline"
        })
    
    def update_device_status(self, device_id: str, **kwargs):
        """
        更新设备状态
        :param device_id: 设备ID
        :param kwargs: 状态键值对
        """
        if device_id not in self._status:
            self._status[device_id] = {
                "is_running": False,
                "remain_time": 0,
                "visited": 0,
                "connection_status": "offline"
            }
        self._status[device_id].update(kwargs)
    
    def stop_task(self, device_id: str):
        """
        停止设备上的任务
        :param device_id: 设备ID
        """
        self._stop_flag[device_id] = True
        self.logger.info(f"已请求停止设备 {device_id} 的任务")
    
    def is_stop_requested(self, device_id: str) -> bool:
        """
        检查是否有停止请求
        :param device_id: 设备ID
        :return: 是否有停止请求
        """
        return self._stop_flag.get(device_id, False)
    
    def disconnect_device(self, device_id: str):
        """
        断开设备连接
        :param device_id: 设备ID
        """
        if device_id in self._devices_pool:
            del self._devices_pool[device_id]
        if device_id in self._status:
            del self._status[device_id]
        if device_id in self._stop_flag:
            del self._stop_flag[device_id]
        self.logger.info(f"已断开设备连接: {device_id}")
    
    def get_connected_devices(self) -> List[str]:
        """
        获取已连接的设备ID列表
        :return: 设备ID列表
        """
        return list(self._devices_pool.keys())
    
    def is_device_connected(self, device_id: str) -> bool:
        """
        检查设备是否已连接
        :param device_id: 设备ID
        :return: 是否已连接
        """
        return device_id in self._devices_pool
    
    def _load_device_aliases(self):
        """
        从配置文件加载设备别名
        """
        try:
            config = self.config_manager.load_config()
            if "device_aliases" in config:
                self._device_aliases = config["device_aliases"]
                self.logger.info("已从配置文件加载设备别名")
        except Exception as e:
            self.logger.error(f"加载设备别名失败: {e}")
    
    def _save_device_aliases(self):
        """
        保存设备别名到配置文件
        """
        try:
            config = self.config_manager.load_config()
            config["device_aliases"] = self._device_aliases
            self.config_manager.save_config(config)
            self.logger.info("已保存设备别名到配置文件")
        except Exception as e:
            self.logger.error(f"保存设备别名失败: {e}")
    
    def set_device_alias(self, device_id: str, alias: str):
        """
        设置设备别名
        :param device_id: 设备ID
        :param alias: 设备别名
        """
        self._device_aliases[device_id] = alias
        self._save_device_aliases()
        self.logger.info(f"已为设备 {device_id} 设置别名: {alias}")
    
    def get_device_alias(self, device_id: str) -> str:
        """
        获取设备别名
        :param device_id: 设备ID
        :return: 设备别名，若未设置返回None
        """
        return self._device_aliases.get(device_id)
    
    def remove_device_alias(self, device_id: str):
        """
        移除设备别名
        :param device_id: 设备ID
        """
        if device_id in self._device_aliases:
            del self._device_aliases[device_id]
            self._save_device_aliases()
            self.logger.info(f"已移除设备 {device_id} 的别名")