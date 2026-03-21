import requests
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from db_manager import DBManager
from machine_code import get_machine_code

logger = logging.getLogger(__name__)


class LicenseManager:
    """授权管理类"""
    
    def __init__(self, api_base_url: str = "https://1259223433-0gnwuwcg9e.ap-beijing.tencentscf.com/v1", api_key: str = "wenyang666"):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.db_manager = DBManager()
        self.machine_code = get_machine_code()
    
    def verify_activation_code(self, auth_code: str, plugin_version: str = "1.0.0") -> Tuple[bool, str, Optional[Dict]]:
        """
        验证激活码
        :param auth_code: 激活码
        :param plugin_version: 插件版本
        :return: (是否成功, 消息, 授权数据)
        """
        url = f"{self.api_base_url}/auth/verify"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        payload = {
            "auth_code": auth_code,
            "machine_code": self.machine_code,
            "client_type": "pc-client",
            "plugin_version": plugin_version
        }
        
        try:
            logger.info(f"正在验证激活码: {auth_code[:10]}...")
            
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                result = response.json()
            except (requests.exceptions.RequestException, ValueError) as e:
                logger.warning(f"云端验证失败，使用本地模拟验证: {e}")
                result = self._mock_verify(auth_code)
            
            if result.get("status") == "valid":
                data = result.get("data", {})
                
                package_type = data.get("package_type", "basic")
                expire_date = data.get("expire_date", data.get("expiry_date", ""))
                max_devices = data.get("max_devices", 2)
                max_daily_minutes = data.get("max_daily_minutes", 120)
                
                success = self.db_manager.save_user_license(
                    auth_code, self.machine_code, package_type,
                    expire_date, max_devices, max_daily_minutes
                )
                
                if success:
                    logger.info(f"激活码验证成功: {package_type}")
                    return True, "激活码验证成功", data
                else:
                    return False, "保存授权信息失败", None
            else:
                message = result.get("message", "激活码验证失败")
                logger.warning(f"激活码验证失败: {message}")
                return False, message, None
                
        except Exception as e:
            logger.error(f"验证激活码异常: {e}")
            return False, f"验证异常: {str(e)}", None
    
    def _mock_verify(self, auth_code: str) -> Dict:
        """模拟验证激活码（开发用）"""
        if auth_code.startswith("TEST_"):
            return {
                "status": "valid",
                "message": "激活码验证成功",
                "data": {
                    "package_type": "premium",
                    "expire_date": "2026-12-31",
                    "expiry_date": "2026-12-31T23:59:59Z",
                    "max_devices": 3,
                    "max_daily_minutes": 300,
                    "machine_code": self.machine_code
                }
            }
        else:
            return {
                "status": "invalid",
                "message": "无效的激活码",
                "data": None
            }
    
    def get_license_info(self) -> Optional[Dict]:
        """获取当前授权信息"""
        return self.db_manager.get_user_license()
    
    def check_launch_permission(self) -> Tuple[bool, str]:
        """
        检查启动权限
        :return: (是否允许启动, 消息)
        """
        license_info = self.get_license_info()
        if not license_info:
            return False, "未激活，请先输入激活码"
        
        if not license_info.get("active"):
            return False, "授权已失效"
        
        today = datetime.now().date().isoformat()
        expire_date_str = license_info.get("expire_date", "")
        try:
            if expire_date_str:
                if "T" in expire_date_str:
                    expire_date = datetime.fromisoformat(expire_date_str.replace("Z", "")).date()
                else:
                    expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d").date()
                
                if datetime.now().date() > expire_date:
                    return False, "授权已过期"
        except Exception as e:
            logger.warning(f"解析过期日期失败: {e}")
        
        return True, "权限检查通过"
    
    def check_daily_limit(self, device_id: str, additional_minutes: int = 0) -> Tuple[bool, str]:
        """
        检查每日时长限制
        :param device_id: 设备ID
        :param additional_minutes: 额外需要的分钟数
        :return: (是否允许, 消息)
        """
        license_info = self.get_license_info()
        if not license_info:
            return False, "未激活"
        
        max_daily = license_info.get("max_daily_minutes", 120)
        if max_daily == -1:
            return True, "无时长限制"
        
        usage = self.db_manager.get_daily_usage(device_id)
        current = usage.get("total_minutes", 0) if usage else 0
        
        if current + additional_minutes > max_daily:
            remaining = max(0, max_daily - current)
            return False, f"今日时长已达上限，剩余可用 {remaining} 分钟"
        
        return True, f"今日还可使用 {max_daily - current - additional_minutes} 分钟"
    
    def record_usage_start(self, device_id: str):
        """记录使用开始"""
        self.db_manager.update_daily_usage(device_id, increment_start=True)
    
    def record_usage_minutes(self, device_id: str, minutes: int):
        """记录使用时长"""
        self.db_manager.update_daily_usage(device_id, minutes=minutes)
    
    def get_device_usage_today(self, device_id: str) -> Optional[Dict]:
        """获取设备今日使用情况"""
        return self.db_manager.get_daily_usage(device_id)
    
    def get_all_devices_usage_today(self):
        """获取所有设备今日使用情况"""
        return self.db_manager.get_all_devices_usage_today()
