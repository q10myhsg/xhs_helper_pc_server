
"""
授权管理模块 - 商业化权限控制
功能：
- 本地 SQLite 存储授权信息
- 每日使用次数统计（养号、创作、导出、主图、封面）
- 权限检查
- 自动清理过期数据
- 云端激活码验证
- 服务端套餐配置获取（含重试和本地缓存）
"""

import sqlite3
import os
import time
import json
import atexit
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

# 默认套餐配置（当服务端不可用时使用）
# 约定：-1 表示不限制
DEFAULT_PACKAGE_CONFIG = {
    "free": {
        "max_devices": 1,
        "max_daily_yanghao": 3,
        "max_daily_create": 5,
        "max_daily_export": 10,
        "max_daily_main_image": 5,
        "max_daily_cover_image": 5,
        "max_single_yanghao_minutes": 20,
        "daily_yanghao_device_limit": True,
    },
    "basic": {
        "max_devices": 3,
        "max_daily_yanghao": 9,
        "max_daily_create": 15,
        "max_daily_export": 30,
        "max_daily_main_image": 15,
        "max_daily_cover_image": 15,
        "max_single_yanghao_minutes": 60,
        "daily_yanghao_device_limit": False,
    },
    "advanced": {
        "max_devices": -1,
        "max_daily_yanghao": -1,
        "max_daily_create": -1,
        "max_daily_export": -1,
        "max_daily_main_image": -1,
        "max_daily_cover_image": -1,
        "max_single_yanghao_minutes": -1,
        "daily_yanghao_device_limit": False,
    }
}

# 默认免费授权配置
DEFAULT_FREE_LICENSE = {
    "package_type": "free",
    "expire_date": None,
    **DEFAULT_PACKAGE_CONFIG["free"]
}

# 配置文件路径
CONFIG_DIR = "config"
DB_PATH = os.path.join(CONFIG_DIR, "license.db")
API_CONFIG_PATH = os.path.join(CONFIG_DIR, "api_config.json")
PACKAGE_CONFIG_PATH = os.path.join(CONFIG_DIR, "package_config.json")
PACKAGE_FETCH_DATE_PATH = os.path.join(CONFIG_DIR, "package_fetch_date.json")

# 全局变量用于退出钩子统计
_current_start_time: Optional[float] = None
_current_device_id: Optional[str] = None

class LicenseManager:
    def __init__(self):
        self.DB_PATH = DB_PATH
        self._load_api_config()
        self._init_db()
        atexit.register(self._exit_hook)
        
        # 初始化套餐配置
        self.package_config = self._load_package_config()
        self._fetch_package_config_if_needed()
    
    def _load_api_config(self):
        """加载 API 配置"""
        self.api_base_url = "https://1259223433-0gnwuwcg9e.ap-beijing.tencentscf.com"
        self.api_key = "wenyang666"
        
        if os.path.exists(API_CONFIG_PATH):
            try:
                with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "api_base_url" in config:
                        self.api_base_url = config["api_base_url"]
                    if "api_key" in config:
                        self.api_key = config["api_key"]
            except Exception:
                pass
    
    def _load_package_config(self) -&gt; Dict[str, Any]:
        """加载本地缓存的套餐配置"""
        if os.path.exists(PACKAGE_CONFIG_PATH):
            try:
                with open(PACKAGE_CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_PACKAGE_CONFIG.copy()
    
    def _save_package_config(self, config: Dict[str, Any]):
        """保存套餐配置到本地缓存"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(PACKAGE_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.package_config = config
        except Exception:
            pass
    
    def _get_last_fetch_date(self) -&gt; Optional[str]:
        """获取上次获取套餐配置的日期"""
        if os.path.exists(PACKAGE_FETCH_DATE_PATH):
            try:
                with open(PACKAGE_FETCH_DATE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("date")
            except Exception:
                pass
        return None
    
    def _save_last_fetch_date(self, date: str):
        """保存获取套餐配置的日期"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(PACKAGE_FETCH_DATE_PATH, "w", encoding="utf-8") as f:
                json.dump({"date": date}, f)
        except Exception:
            pass
    
    def _fetch_package_config_from_server(self) -&gt; Optional[Dict[str, Any]]:
        """从服务端获取套餐配置"""
        url = f"{self.api_base_url}/package/config"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            result = resp.json()
            if result.get("status") != "success":
                return None
            
            return result.get("data")
        except Exception:
            return None
    
    def _fetch_package_config_if_needed(self):
        """每天第一次启动时从服务端获取套餐配置"""
        today = datetime.now().strftime("%Y-%m-%d")
        last_fetch_date = self._get_last_fetch_date()
        
        if last_fetch_date == today:
            # 今天已经获取过了
            return
        
        # 尝试获取，最多重试3次
        config = None
        for attempt in range(3):
            config = self._fetch_package_config_from_server()
            if config:
                break
            if attempt &lt; 2:
                time.sleep(5)
        
        if config:
            # 获取成功
            self._save_package_config(config)
            self._save_last_fetch_date(today)
        else:
            # 获取失败，使用本地缓存或默认配置
            pass
    
    def _init_db(self):
        """初始化数据库表"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # 设备注册信息
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registered_devices (
            device_id TEXT PRIMARY KEY,
            device_alias TEXT,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            activated BOOLEAN DEFAULT 1
        )
        """)
        
        # 每日使用次数统计表（新）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage_count (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            use_date TEXT NOT NULL,
            yanghao_count INTEGER DEFAULT 0,
            create_count INTEGER DEFAULT 0,
            export_count INTEGER DEFAULT 0,
            main_image_count INTEGER DEFAULT 0,
            cover_image_count INTEGER DEFAULT 0,
            yanghao_device_id TEXT,
            update_time TEXT NOT NULL,
            UNIQUE(device_id, use_date)
        )
        """)
        
        # 用户授权信息
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_license (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activation_code TEXT UNIQUE NOT NULL,
            machine_code TEXT UNIQUE,
            package_type TEXT NOT NULL,
            expire_date TEXT,
            max_devices INTEGER NOT NULL,
            max_daily_yanghao INTEGER NOT NULL,
            max_daily_create INTEGER NOT NULL,
            max_daily_export INTEGER NOT NULL,
            max_daily_main_image INTEGER NOT NULL,
            max_daily_cover_image INTEGER NOT NULL,
            max_single_yanghao_minutes INTEGER NOT NULL,
            daily_yanghao_device_limit BOOLEAN DEFAULT 0,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
        """)
        
        conn.commit()
        conn.close()
    
    def _exit_hook(self):
        """程序退出钩子，确保统计时长"""
        global _current_start_time, _current_device_id
        if _current_start_time and _current_device_id:
            end_time = time.time()
            used_minutes = int((end_time - _current_start_time) / 60)
            if used_minutes &lt; 1:
                used_minutes = 1
            self._add_usage(_current_device_id, self._get_today(), used_minutes)
    
    def _get_today(self) -&gt; str:
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_current_year_month(self) -&gt; str:
        """获取当前年月 YYYY-MM"""
        return datetime.now().strftime("%Y-%m")
    
    def _clean_old_records(self, conn):
        """删除 7 天前的记录"""
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        conn.execute("DELETE FROM daily_usage_count WHERE use_date &lt; ?", (seven_days_ago,))
        conn.commit()
    
    def _add_usage(self, device_id: str, date: str, minutes: int):
        """增加使用时长统计（兼容旧版，暂时保留）"""
        pass  # 新版不再统计时长
    
    def _increment_daily_count(self, device_id: str, date: str, count_type: str):
        """增加每日使用次数统计
        
        Args:
            device_id: 设备ID
            date: 日期 (YYYY-MM-DD)
            count_type: 计数类型 ('yanghao', 'create', 'export', 'main_image', 'cover_image')
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # 查询是否已有今日记录
        cursor.execute("""
        SELECT yanghao_count, create_count, export_count, main_image_count, cover_image_count, yanghao_device_id
        FROM daily_usage_count 
        WHERE device_id = ? AND use_date = ?
        """, (device_id, date))
        row = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if row:
            yanghao_count, create_count, export_count, main_image_count, cover_image_count, yanghao_device_id = row
            
            if count_type == 'yanghao':
                yanghao_count += 1
                # 如果是免费版，记录今天养号的设备
                license = self.get_current_license()
                if license.get('daily_yanghao_device_limit', False):
                    yanghao_device_id = device_id
            elif count_type == 'create':
                create_count += 1
            elif count_type == 'export':
                export_count += 1
            elif count_type == 'main_image':
                main_image_count += 1
            elif count_type == 'cover_image':
                cover_image_count += 1
            
            cursor.execute("""
            UPDATE daily_usage_count 
            SET yanghao_count = ?, create_count = ?, export_count = ?, 
                main_image_count = ?, cover_image_count = ?, yanghao_device_id = ?, update_time = ?
            WHERE device_id = ? AND use_date = ?
            """, (yanghao_count, create_count, export_count, main_image_count, cover_image_count, yanghao_device_id, now, device_id, date))
        else:
            yanghao_count = 1 if count_type == 'yanghao' else 0
            create_count = 1 if count_type == 'create' else 0
            export_count = 1 if count_type == 'export' else 0
            main_image_count = 1 if count_type == 'main_image' else 0
            cover_image_count = 1 if count_type == 'cover_image' else 0
            
            # 如果是免费版，记录今天养号的设备
            yanghao_device_id = None
            if count_type == 'yanghao':
                license = self.get_current_license()
                if license.get('daily_yanghao_device_limit', False):
                    yanghao_device_id = device_id
            
            cursor.execute("""
            INSERT INTO daily_usage_count 
            (device_id, use_date, yanghao_count, create_count, export_count, 
             main_image_count, cover_image_count, yanghao_device_id, update_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (device_id, date, yanghao_count, create_count, export_count, 
                  main_image_count, cover_image_count, yanghao_device_id, now))
        
        self._clean_old_records(conn)
        conn.commit()
        conn.close()
    
    def get_daily_usage(self, device_id: str, date: str) -&gt; Dict[str, int]:
        """获取当日已使用次数
        
        Returns:
            {
                'yanghao_count': 养号次数,
                'create_count': 创作次数,
                'export_count': 导出次数,
                'main_image_count': 主图次数,
                'cover_image_count': 封面次数,
                'yanghao_device_id': 今日养号设备ID
            }
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT yanghao_count, create_count, export_count, main_image_count, cover_image_count, yanghao_device_id
        FROM daily_usage_count 
        WHERE device_id = ? AND use_date = ?
        """, (device_id, date))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'yanghao_count': row[0] or 0,
                'create_count': row[1] or 0,
                'export_count': row[2] or 0,
                'main_image_count': row[3] or 0,
                'cover_image_count': row[4] or 0,
                'yanghao_device_id': row[5],
            }
        return {
            'yanghao_count': 0,
            'create_count': 0,
            'export_count': 0,
            'main_image_count': 0,
            'cover_image_count': 0,
            'yanghao_device_id': None,
        }
    
    def get_total_daily_usage_all_devices(self) -&gt; Dict[str, int]:
        """获取今日所有设备总使用次数"""
        today = self._get_today()
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT SUM(yanghao_count), SUM(create_count), SUM(export_count), 
               SUM(main_image_count), SUM(cover_image_count), 
               MAX(yanghao_device_id)
        FROM daily_usage_count WHERE use_date = ?
        """, (today,))
        row = cursor.fetchone()
        conn.close()
        
        return {
            'yanghao_count': row[0] or 0,
            'create_count': row[1] or 0,
            'export_count': row[2] or 0,
            'main_image_count': row[3] or 0,
            'cover_image_count': row[4] or 0,
            'yanghao_device_id': row[5],
        }
    
    def check_daily_quota(self, count_type: str, device_id: str = None) -&gt; Tuple[bool, str]:
        """检查每日配额是否够用
        
        Args:
            count_type: 计数类型 ('yanghao', 'create', 'export', 'main_image', 'cover_image')
            device_id: 设备ID（仅养号时需要）
        
        Returns:
            (can_proceed, message)
        """
        license = self.get_current_license()
        today = self._get_today()
        daily_usage = self.get_total_daily_usage_all_devices()
        
        max_key = f"max_daily_{count_type}"
        used_key = f"{count_type}_count"
        
        max_count = license.get(max_key, -1)
        used_count = daily_usage.get(used_key, 0)
        
        # 检查是否超限
        if max_count != -1 and used_count &gt;= max_count:
            type_names = {
                'yanghao': '养号',
                'create': '创作',
                'export': '导出',
                'main_image': '主图生成',
                'cover_image': '封面生成',
            }
            type_name = type_names.get(count_type, count_type)
            return False, f"今日已使用 {used_count}/{max_count} 次{type_name}次数，达到今日限额，请明天再来或升级套餐"
        
        # 如果是养号，检查设备限制（免费版）
        if count_type == 'yanghao' and device_id:
            if license.get('daily_yanghao_device_limit', False):
                yanghao_device_id = daily_usage.get('yanghao_device_id')
                if yanghao_device_id and yanghao_device_id != device_id:
                    return False, "免费版每天只能在一个设备上养号，请明天再试或升级套餐"
        
        return True, ""
    
    def increment_daily_yanghao(self, device_id: str):
        """增加每日养号次数"""
        today = self._get_today()
        self._increment_daily_count(device_id, today, 'yanghao')
    
    def increment_daily_create(self, device_id: str):
        """增加每日创作次数"""
        today = self._get_today()
        self._increment_daily_count(device_id, today, 'create')
    
    def increment_daily_export(self, device_id: str):
        """增加每日导出次数"""
        today = self._get_today()
        self._increment_daily_count(device_id, today, 'export')
    
    def increment_daily_main_image(self, device_id: str):
        """增加每日主图生成次数"""
        today = self._get_today()
        self._increment_daily_count(device_id, today, 'main_image')
    
    def increment_daily_cover_image(self, device_id: str):
        """增加每日封面生成次数"""
        today = self._get_today()
        self._increment_daily_count(device_id, today, 'cover_image')
    
    def get_registered_devices_count(self) -&gt; int:
        """获取已注册设备数量"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registered_devices WHERE activated = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    def get_current_license(self) -&gt; Dict[str, Any]:
        """获取当前有效的授权"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT activation_code, package_type, expire_date, max_devices, 
               max_daily_yanghao, max_daily_create, max_daily_export, 
               max_daily_main_image, max_daily_cover_image, 
               max_single_yanghao_minutes, daily_yanghao_device_limit, active
        FROM user_license WHERE active = 1 ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # 返回默认免费授权
            return DEFAULT_FREE_LICENSE.copy()
        
        if not row[11]:
            # 授权不活跃，返回免费
            return DEFAULT_FREE_LICENSE.copy()
        
        # 检查是否过期
        expire_date = row[2]
        if expire_date:
            try:
                expire_dt = datetime.strptime(expire_date, "%Y-%m-%d")
                if datetime.now() &gt; expire_dt:
                    # 已过期，返回免费
                    return DEFAULT_FREE_LICENSE.copy()
            except:
                pass
        
        # 从服务端套餐配置中获取配额（优先使用服务端配置）
        package_type = row[1]
        package_config = self.package_config.get(package_type, {})
        
        return {
            "package_type": package_type,
            "expire_date": row[2],
            "max_devices": package_config.get("max_devices", row[3]),
            "max_daily_yanghao": package_config.get("max_daily_yanghao", row[4]),
            "max_daily_create": package_config.get("max_daily_create", row[5]),
            "max_daily_export": package_config.get("max_daily_export", row[6]),
            "max_daily_main_image": package_config.get("max_daily_main_image", row[7]),
            "max_daily_cover_image": package_config.get("max_daily_cover_image", row[8]),
            "max_single_yanghao_minutes": package_config.get("max_single_yanghao_minutes", row[9]),
            "daily_yanghao_device_limit": package_config.get("daily_yanghao_device_limit", bool(row[10])),
            "activation_code": row[0],
        }
    
    def activate_license(self, activation_code: str, machine_code: str) -&gt; Tuple[bool, str]:
        """调用云端API激活授权"""
        # 请求云端 - 对齐官方接口协议
        url = f"{self.api_base_url}/auth/verify"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "auth_code": activation_code,
            "machine_code": machine_code,
            "client_type": "pc-client",
            "plugin_version": "1.0.0",
        }
        
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=10)
            if resp.status_code != 200:
                return False, f"服务器返回错误: {resp.status_code}"
            
            result = resp.json()
            if result.get("status") != "valid":
                return False, result.get("message", "激活码无效")
            
            license_data = result.get("data", {})
            package_type = license_data.get("package_type", "basic")
            expire_date = license_data.get("expiry_date")
            
            # 从服务端套餐配置中获取配额
            package_config = self.package_config.get(package_type, {})
            
            # 使用服务端返回的或本地默认的配额
            max_devices = license_data.get("max_devices", package_config.get("max_devices", 3))
            max_daily_yanghao = license_data.get("max_daily_yanghao", package_config.get("max_daily_yanghao", 9))
            max_daily_create = license_data.get("max_daily_create", package_config.get("max_daily_create", 15))
            max_daily_export = license_data.get("max_daily_export", package_config.get("max_daily_export", 30))
            max_daily_main_image = license_data.get("max_daily_main_image", package_config.get("max_daily_main_image", 15))
            max_daily_cover_image = license_data.get("max_daily_cover_image", package_config.get("max_daily_cover_image", 15))
            max_single_yanghao_minutes = license_data.get("max_single_yanghao_minutes", package_config.get("max_single_yanghao_minutes", 60))
            daily_yanghao_device_limit = license_data.get("daily_yanghao_device_limit", package_config.get("daily_yanghao_device_limit", False))
            
            # 转换过期日期：从 ISO 格式提取 YYYY-MM-DD
            if expire_date and 'T' in expire_date:
                expire_date = expire_date.split('T')[0]
            
        except Exception as e:
            return False, f"网络请求失败: {str(e)}"
        
        # 保存到本地
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # 先禁用旧授权
        cursor.execute("UPDATE user_license SET active = 0")
        
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO user_license 
        (activation_code, machine_code, package_type, expire_date, 
         max_devices, max_daily_yanghao, max_daily_create, max_daily_export,
         max_daily_main_image, max_daily_cover_image, 
         max_single_yanghao_minutes, daily_yanghao_device_limit,
         create_time, update_time, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (activation_code, machine_code, package_type, expire_date, 
              max_devices, max_daily_yanghao, max_daily_create, max_daily_export,
              max_daily_main_image, max_daily_cover_image,
              max_single_yanghao_minutes, daily_yanghao_device_limit, now, now))
        
        conn.commit()
        conn.close()
        
        return True, f"激活成功！套餐: {package_type}"
    
    def check_can_start(self, device_id: str, planned_duration: int = 0, is_create: bool = False) -&gt; Tuple[bool, str, int]:
        """检查是否可以启动养号/创作
        
        Args:
            device_id: 设备ID
            planned_duration: 用户计划养号时长（分钟）
            is_create: 是否是内容创作
        
        Returns:
            (can_start, message, actual_duration)
            - can_start: 是否可以启动
            - message: 提示消息
            - actual_duration: 实际可以运行的时长
        """
        license = self.get_current_license()
        max_devices = license["max_devices"]
        max_single_duration = license.get("max_single_yanghao_minutes", -1)
        
        # 检查养号次数配额
        ok, msg = self.check_daily_quota('yanghao', device_id)
        if not ok:
            return False, msg, 0
        
        # 如果是创作，检查创作配额
        if is_create:
            ok, msg = self.check_daily_quota('create', device_id)
            if not ok:
                return False, msg, 0
        
        # 检查设备数量
        device_count = self.get_registered_devices_count()
        if max_devices != -1 and device_count &gt; max_devices:
            return False, f"已达到最大设备数限制({max_devices})，请升级套餐", 0
        
        # 检查单次养号时长
        actual_duration = planned_duration
        message = ""
        
        if max_single_duration != -1:
            if planned_duration &gt; max_single_duration:
                actual_duration = max_single_duration
                message = (f"⚠️ 套餐单次养号最长 {max_single_duration} 分钟，"
                           f"你计划养号 {planned_duration} 分钟，本次将只运行 {max_single_duration} 分钟后自动停止")
        
        if message:
            return True, message, actual_duration
        else:
            return True, "可以启动", actual_duration
    
    def on_start(self, device_id: str):
        """启动前调用，记录开始时间并增加养号次数"""
        global _current_start_time, _current_device_id
        _current_start_time = time.time()
        _current_device_id = device_id
        # 增加养号次数
        self.increment_daily_yanghao(device_id)
    
    def on_stop(self, device_id: str):
        """停止后调用"""
        global _current_start_time, _current_device_id
        if _current_start_time and _current_device_id == device_id:
            _current_start_time = None
            _current_device_id = None
    
    def get_usage_stats(self) -&gt; Dict[str, Any]:
        """获取使用统计信息"""
        today = self._get_today()
        ym = self._get_current_year_month()
        license = self.get_current_license()
        daily_usage = self.get_total_daily_usage_all_devices()
        
        # 获取每个设备今日使用情况
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT device_id, yanghao_count, create_count, export_count, 
               main_image_count, cover_image_count
        FROM daily_usage_count WHERE use_date = ?
        """, (today,))
        rows = cursor.fetchall()
        device_usage = {}
        for row in rows:
            device_usage[row[0]] = {
                'yanghao_count': row[1] or 0,
                'create_count': row[2] or 0,
                'export_count': row[3] or 0,
                'main_image_count': row[4] or 0,
                'cover_image_count': row[5] or 0,
            }
        conn.close()
        
        return {
            "today": today,
            "year_month": ym,
            "license": license,
            "used_daily_yanghao": daily_usage['yanghao_count'],
            "used_daily_create": daily_usage['create_count'],
            "used_daily_export": daily_usage['export_count'],
            "used_daily_main_image": daily_usage['main_image_count'],
            "used_daily_cover_image": daily_usage['cover_image_count'],
            "today_yanghao_device_id": daily_usage.get('yanghao_device_id'),
            "device_usage": device_usage,
            "registered_devices_count": self.get_registered_devices_count(),
        }
    
    def refresh_license(self) -&gt; Tuple[bool, str]:
        """程序启动时刷新授权，联网更新"""
        # 获取当前激活码
        current = self.get_current_license()
        if "activation_code" not in current or not current.get("activation_code"):
            # 没有激活码，不用刷新，用默认
            return True, "使用免费授权"
        
        # 获取机器码
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT machine_code FROM user_license 
        WHERE activation_code = ? AND active = 1
        """, (current["activation_code"],))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return True, "使用本地缓存授权"
        
        machine_code = row[0]
        activation_code = current["activation_code"]
        
        # 重新验证
        url = f"{self.api_base_url}/auth/verify"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "auth_code": activation_code,
            "machine_code": machine_code,
            "client_type": "pc-client",
            "plugin_version": "1.0.0",
        }
        
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=10)
            if resp.status_code != 200:
                # 网络失败，使用缓存
                return True, "使用本地缓存授权，网络验证失败"
            
            result = resp.json()
            if result.get("status") != "valid":
                # 授权失效
                return False, "授权已失效，请重新激活"
            
            license_data = result.get("data", {})
            package_type = license_data.get("package_type", current["package_type"])
            expire_date = license_data.get("expiry_date")
            
            # 从服务端套餐配置中获取配额
            package_config = self.package_config.get(package_type, {})
            
            max_devices = license_data.get("max_devices", package_config.get("max_devices", current.get("max_devices", 3)))
            max_daily_yanghao = license_data.get("max_daily_yanghao", package_config.get("max_daily_yanghao", current.get("max_daily_yanghao", 9)))
            max_daily_create = license_data.get("max_daily_create", package_config.get("max_daily_create", current.get("max_daily_create", 15)))
            max_daily_export = license_data.get("max_daily_export", package_config.get("max_daily_export", current.get("max_daily_export", 30)))
            max_daily_main_image = license_data.get("max_daily_main_image", package_config.get("max_daily_main_image", current.get("max_daily_main_image", 15)))
            max_daily_cover_image = license_data.get("max_daily_cover_image", package_config.get("max_daily_cover_image", current.get("max_daily_cover_image", 15)))
            max_single_yanghao_minutes = license_data.get("max_single_yanghao_minutes", package_config.get("max_single_yanghao_minutes", current.get("max_single_yanghao_minutes", 60)))
            daily_yanghao_device_limit = license_data.get("daily_yanghao_device_limit", package_config.get("daily_yanghao_device_limit", current.get("daily_yanghao_device_limit", False)))
            
            # 转换过期日期：从 ISO 格式提取 YYYY-MM-DD
            if expire_date and 'T' in expire_date:
                expire_date = expire_date.split('T')[0]
            
            # 更新本地缓存
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
            UPDATE user_license 
            SET package_type = ?, expire_date = ?, max_devices = ?, 
                max_daily_yanghao = ?, max_daily_create = ?, max_daily_export = ?,
                max_daily_main_image = ?, max_daily_cover_image = ?,
                max_single_yanghao_minutes = ?, daily_yanghao_device_limit = ?,
                update_time = ?
            WHERE activation_code = ?
            """, (package_type, expire_date, max_devices, 
                  max_daily_yanghao, max_daily_create, max_daily_export,
                  max_daily_main_image, max_daily_cover_image,
                  max_single_yanghao_minutes, daily_yanghao_device_limit,
                  now, activation_code))
            conn.commit()
            conn.close()
            
            return True, "授权信息已更新"
        
        except Exception as e:
            # 网络失败，使用缓存
            return True, f"使用本地缓存授权，网络异常: {str(e)}"

# 单例
_