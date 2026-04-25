
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
from machine_code import get_machine_code

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
        "max_daily_transfer": 10,
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
        "max_daily_transfer": 30,
        "max_single_yanghao_minutes": 60,
        "daily_yanghao_device_limit": False,
    },
    "premium": {
        "max_devices": -1,
        "max_daily_yanghao": -1,
        "max_daily_create": -1,
        "max_daily_export": -1,
        "max_daily_main_image": -1,
        "max_daily_cover_image": -1,
        "max_daily_transfer": -1,
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
        
        # 初始化机器码
        self.machine_code = get_machine_code()
        
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
    
    def _load_package_config(self) -> Dict[str, Any]:
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
    
    def _get_last_fetch_date(self) -> Optional[str]:
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
    
    def _fetch_package_config_from_server(self) -> Optional[Dict[str, Any]]:
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
    
    def fetch_device_info_from_server(self, machine_code: str = None) -> Optional[Dict[str, Any]]:
        """从服务端获取设备信息和权限配置
        
        对应接口协议: POST /device/info
        """
        if not machine_code:
            machine_code = self.machine_code
            
        url = f"{self.api_base_url}/device/info"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "machine_code": machine_code,
            "client_type": "pc-client",
            "plugin_version": "1.0.0",
        }
        
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"获取设备信息失败: HTTP {resp.status_code}")
                return None
            
            result = resp.json()
            if result.get("status") != "success":
                print(f"获取设备信息失败: {result.get('message', '未知错误')}")
                return None
            
            return result.get("data")
        except Exception as e:
            print(f"获取设备信息异常: {str(e)}")
            return None
    
    def _parse_permissions_from_protocol(self, permissions: Dict[str, Any]) -> Dict[str, Any]:
        """将协议中的 permissions 结构解析为本地使用的配置格式
        
        协议格式:
        {
            "auto_use": {"device_count": 3, "device_time": 60},
            "pdf": {"daily_limit": 30},
            "cover": {"daily_limit": 30},
            "transfer": {"daily_limit": 30}
        }
        
        本地格式:
        {
            "max_devices": 3,
            "max_daily_yanghao": 9,
            "max_daily_create": 15,
            "max_daily_export": 30,
            "max_daily_main_image": 15,
            "max_daily_cover_image": 15,
            "max_single_yanghao_minutes": 60,
            "daily_yanghao_device_limit": False,
        }
        """
        if not permissions:
            return {}
        
        parsed = {}
        
        # 解析 auto_use 权限
        auto_use = permissions.get("auto_use", {})
        if auto_use:
            parsed["max_devices"] = auto_use.get("device_count", 3)
            parsed["max_single_yanghao_minutes"] = auto_use.get("device_time", 60)
        
        # 解析 pdf 权限 (对应导出次数)
        pdf = permissions.get("pdf", {})
        if pdf:
            parsed["max_daily_export"] = pdf.get("daily_limit", 30)
        
        # 解析 cover 权限 (对应封面生成次数)
        cover = permissions.get("cover", {})
        if cover:
            parsed["max_daily_cover_image"] = cover.get("daily_limit", 30)
        
        # 解析 transfer 权限 (对应文件传输次数)
        transfer = permissions.get("transfer", {})
        if transfer:
            parsed["max_daily_transfer"] = transfer.get("daily_limit", 30)
        
        # 其他字段使用默认值或从其他来源获取
        # 养号次数和创作次数可能需要从其他配置获取
        parsed.setdefault("max_daily_yanghao", 9)
        parsed.setdefault("max_daily_create", 15)
        parsed.setdefault("max_daily_main_image", 15)
        
        # 根据套餐类型设置 device_limit
        # 免费版有限制，其他版本没有
        parsed["daily_yanghao_device_limit"] = parsed.get("max_devices", 3) == 1
        
        return parsed
    
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
            if attempt < 2:
                time.sleep(5)
        
        if config:
            # 获取成功
            self._save_package_config(config)
            self._save_last_fetch_date(today)
        else:
            # 获取失败，使用本地缓存或默认配置
            pass
    
    def _init_db(self):
        """初始化数据库表 - 包含迁移逻辑"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # ============== 设备注册信息表 ==============
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registered_devices (
            device_id TEXT PRIMARY KEY,
            device_alias TEXT,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            activated BOOLEAN DEFAULT 1
        )
        """)
        
        # ============== 每日使用次数统计表 ==============
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
            transfer_count INTEGER DEFAULT 0,
            yanghao_device_id TEXT,
            update_time TEXT NOT NULL,
            UNIQUE(device_id, use_date)
        )
        """)
        
        # ============== 用户授权信息表 ==============
        # 先检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_license'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # 表不存在，创建新表
            cursor.execute("""
            CREATE TABLE user_license (
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
        else:
            # 表已存在，检查并添加缺失的列
            self._migrate_user_license_table(cursor)
        
        # 迁移每日使用统计表
        self._migrate_daily_usage_table(cursor)
        
        conn.commit()
        conn.close()
    
    def _migrate_user_license_table(self, cursor):
        """迁移 user_license 表，添加缺失的字段"""
        # 获取当前表的所有列
        cursor.execute("PRAGMA table_info(user_license)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # 定义所有需要的字段及其默认值（SQLite 不允许直接加 NOT NULL 到已有数据的表）
        required_columns = {
            'package_type': ("TEXT", "'free'"),
            'expire_date': ("TEXT", "NULL"),
            'max_devices': ("INTEGER", "1"),
            'max_daily_yanghao': ("INTEGER", "3"),
            'max_daily_create': ("INTEGER", "5"),
            'max_daily_export': ("INTEGER", "10"),
            'max_daily_main_image': ("INTEGER", "5"),
            'max_daily_cover_image': ("INTEGER", "5"),
            'max_single_yanghao_minutes': ("INTEGER", "20"),
            'daily_yanghao_device_limit': ("BOOLEAN", "1"),
            'active': ("BOOLEAN", "1")
        }
        
        # 添加缺失的列
        for col_name, (col_type, default_sql) in required_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE user_license ADD COLUMN {col_name} {col_type} DEFAULT {default_sql}")
                    print(f"数据库迁移: 已添加列 {col_name} (默认值: {default_sql})")
                except Exception as e:
                    print(f"数据库迁移: 添加列 {col_name} 失败: {e}")
    
    def _migrate_daily_usage_table(self, cursor):
        """迁移 daily_usage_count 表，添加缺失的字段"""
        # 获取当前表的所有列
        cursor.execute("PRAGMA table_info(daily_usage_count)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # 添加 transfer_count 字段（如果不存在）
        if 'transfer_count' not in columns:
            try:
                cursor.execute("ALTER TABLE daily_usage_count ADD COLUMN transfer_count INTEGER DEFAULT 0")
                print("数据库迁移: 已添加列 transfer_count (默认值: 0)")
            except Exception as e:
                print(f"数据库迁移: 添加列 transfer_count 失败: {e}")
    
    def _exit_hook(self):
        """程序退出钩子，确保统计时长"""
        global _current_start_time, _current_device_id
        if _current_start_time and _current_device_id:
            end_time = time.time()
            used_minutes = int((end_time - _current_start_time) / 60)
            if used_minutes < 1:
                used_minutes = 1
            self._add_usage(_current_device_id, self._get_today(), used_minutes)
    
    def _get_today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_current_year_month(self) -> str:
        """获取当前年月 YYYY-MM"""
        return datetime.now().strftime("%Y-%m")
    
    def _clean_old_records(self, conn):
        """删除 7 天前的记录"""
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        conn.execute("DELETE FROM daily_usage_count WHERE use_date < ?", (seven_days_ago,))
        conn.commit()
    
    def _add_usage(self, device_id: str, date: str, minutes: int):
        """增加使用时长统计（兼容旧版，暂时保留）"""
        pass  # 新版不再统计时长
    
    def _increment_daily_count(self, device_id: str, date: str, count_type: str):
        """增加每日使用次数统计
        
        Args:
            device_id: 设备ID
            date: 日期 (YYYY-MM-DD)
            count_type: 计数类型 ('yanghao', 'create', 'export', 'main_image', 'cover_image', 'transfer')
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # 查询是否已有今日记录
        cursor.execute("""
        SELECT yanghao_count, create_count, export_count, main_image_count, cover_image_count, transfer_count, yanghao_device_id
        FROM daily_usage_count 
        WHERE device_id = ? AND use_date = ?
        """, (device_id, date))
        row = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if row:
            yanghao_count, create_count, export_count, main_image_count, cover_image_count, transfer_count, yanghao_device_id = row
            
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
            elif count_type == 'transfer':
                transfer_count += 1
            
            cursor.execute("""
            UPDATE daily_usage_count 
            SET yanghao_count = ?, create_count = ?, export_count = ?, 
                main_image_count = ?, cover_image_count = ?, transfer_count = ?, yanghao_device_id = ?, update_time = ?
            WHERE device_id = ? AND use_date = ?
            """, (yanghao_count, create_count, export_count, main_image_count, cover_image_count, transfer_count, yanghao_device_id, now, device_id, date))
        else:
            yanghao_count = 1 if count_type == 'yanghao' else 0
            create_count = 1 if count_type == 'create' else 0
            export_count = 1 if count_type == 'export' else 0
            main_image_count = 1 if count_type == 'main_image' else 0
            cover_image_count = 1 if count_type == 'cover_image' else 0
            transfer_count = 1 if count_type == 'transfer' else 0
            
            # 如果是免费版，记录今天养号的设备
            yanghao_device_id = None
            if count_type == 'yanghao':
                license = self.get_current_license()
                if license.get('daily_yanghao_device_limit', False):
                    yanghao_device_id = device_id
            
            cursor.execute("""
            INSERT INTO daily_usage_count 
            (device_id, use_date, yanghao_count, create_count, export_count, 
             main_image_count, cover_image_count, transfer_count, yanghao_device_id, update_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (device_id, date, yanghao_count, create_count, export_count, 
                  main_image_count, cover_image_count, transfer_count, yanghao_device_id, now))
        
        self._clean_old_records(conn)
        conn.commit()
        conn.close()
    
    def get_daily_usage(self, device_id: str, date: str) -> Dict[str, int]:
        """获取当日已使用次数

        Returns:
            {
                'yanghao_count': 养号次数,
                'create_count': 创作次数,
                'export_count': 导出次数,
                'main_image_count': 主图次数,
                'cover_image_count': 封面次数,
                'transfer_count': 文件传输次数,
                'yanghao_device_id': 今日养号设备ID
            }
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT yanghao_count, create_count, export_count, main_image_count, cover_image_count, transfer_count, yanghao_device_id
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
                'transfer_count': row[5] or 0,
                'yanghao_device_id': row[6],
            }
        return {
            'yanghao_count': 0,
            'create_count': 0,
            'export_count': 0,
            'main_image_count': 0,
            'cover_image_count': 0,
            'transfer_count': 0,
            'yanghao_device_id': None,
        }
    
    def get_total_daily_usage_all_devices(self) -> Dict[str, int]:
        """获取今日所有设备总使用次数"""
        today = self._get_today()
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT SUM(yanghao_count), SUM(create_count), SUM(export_count),
               SUM(main_image_count), SUM(cover_image_count), SUM(transfer_count),
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
            'transfer_count': row[5] or 0,
            'yanghao_device_id': row[6],
        }
    
    def check_daily_quota(self, count_type: str, device_id: str = None) -> Tuple[bool, str]:
        """检查每日配额是否够用

        Args:
            count_type: 计数类型 ('yanghao', 'create', 'export', 'main_image', 'cover_image', 'transfer')
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
        if max_count != -1 and used_count >= max_count:
            type_names = {
                'yanghao': '养号',
                'create': '创作',
                'export': '导出',
                'main_image': '主图生成',
                'cover_image': '封面生成',
                'transfer': '文件传输',
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
    
    def increment_daily_transfer(self, device_id: str):
        """增加每日文件传输次数"""
        today = self._get_today()
        self._increment_daily_count(device_id, today, 'transfer')
    
    def get_registered_devices_count(self) -> int:
        """获取已注册设备数量"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registered_devices WHERE activated = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    def get_current_license(self) -> Dict[str, Any]:
        """获取当前有效的授权"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT activation_code, package_type, expire_date, max_devices, 
               max_daily_yanghao, max_daily_create, max_daily_export, 
               max_daily_main_image, max_daily_cover_image, 
               max_single_yanghao_minutes, daily_yanghao_device_limit, active, create_time
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
                if datetime.now() > expire_dt:
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
            "create_time": row[12],
        }
    
    def activate_license(self, activation_code: str, machine_code: str) -> Tuple[bool, str]:
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
            permissions = license_data.get("permissions", {})
            
            # 从服务端套餐配置中获取配额
            package_config = self.package_config.get(package_type, {})
            
            # 优先使用协议中的 permissions 结构，如果没有则使用本地配置
            if permissions:
                parsed_permissions = self._parse_permissions_from_protocol(permissions)
                max_devices = parsed_permissions.get("max_devices", 3)
                max_daily_yanghao = parsed_permissions.get("max_daily_yanghao", 9)
                max_daily_create = parsed_permissions.get("max_daily_create", 15)
                max_daily_export = parsed_permissions.get("max_daily_export", 30)
                max_daily_main_image = parsed_permissions.get("max_daily_main_image", 15)
                max_daily_cover_image = parsed_permissions.get("max_daily_cover_image", 15)
                max_single_yanghao_minutes = parsed_permissions.get("max_single_yanghao_minutes", 60)
                daily_yanghao_device_limit = parsed_permissions.get("daily_yanghao_device_limit", False)
            else:
                # 使用服务端返回的或本地默认的配额（兼容旧版）
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
        
        # 先检查是否已存在该设备码的授权，如果存在就更新，否则插入
        cursor.execute("SELECT id, create_time FROM user_license WHERE machine_code = ?", (machine_code,))
        existing = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if existing:
            # 更新现有记录
            create_time = existing[1]
            cursor.execute("""
            UPDATE user_license 
            SET activation_code = ?, package_type = ?, expire_date = ?, 
                max_devices = ?, max_daily_yanghao = ?, max_daily_create = ?, 
                max_daily_export = ?, max_daily_main_image = ?, 
                max_daily_cover_image = ?, max_single_yanghao_minutes = ?, 
                daily_yanghao_device_limit = ?, update_time = ?, active = 1
            WHERE machine_code = ?
            """, (activation_code, package_type, expire_date, 
                  max_devices, max_daily_yanghao, max_daily_create, max_daily_export,
                  max_daily_main_image, max_daily_cover_image,
                  max_single_yanghao_minutes, daily_yanghao_device_limit, now, machine_code))
        else:
            # 插入新记录
            cursor.execute("""
            INSERT INTO user_license 
            (activation_code, machine_code, package_type, expire_date, 
             max_devices, max_daily_yanghao, max_daily_create, max_daily_export,
             max_daily_main_image, max_daily_cover_image, 
             max_single_yanghao_minutes, daily_yanghao_device_limit,
             create_time, update_time, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (activation_code, machine_code, package_type, expire_date, 
                  max_devices, max_daily_yanghao, max_daily_create, max_daily_export,
                  max_daily_main_image, max_daily_cover_image,
                  max_single_yanghao_minutes, daily_yanghao_device_limit, now, now))
        
        conn.commit()
        conn.close()
        
        return True, f"激活成功！套餐: {package_type}"
    
    def check_can_start(self, device_id: str, planned_duration: int = 0, is_create: bool = False) -> Tuple[bool, str, int]:
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
        if max_devices != -1 and device_count > max_devices:
            return False, f"已达到最大设备数限制({max_devices})，请升级套餐", 0
        
        # 不再限制时长，只限制次数
        return True, "可以启动", planned_duration
    
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
    
    def get_usage_stats(self) -> Dict[str, Any]:
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
               main_image_count, cover_image_count, transfer_count
        FROM daily_usage_count WHERE use_date = ?
        """, (today,))
        rows = cursor.fetchall()
        device_usage_dict = {}
        for row in rows:
            device_usage_dict[row[0]] = {
                'yanghao_count': row[1] or 0,
                'create_count': row[2] or 0,
                'export_count': row[3] or 0,
                'main_image_count': row[4] or 0,
                'cover_image_count': row[5] or 0,
                'transfer_count': row[6] or 0,
            }
        conn.close()

        # 为了兼容旧页面，添加 active 字段和重命名 device_usage
        license['active'] = license.get('activation_code') is not None
        devices_usage = []
        for device_id, usage in device_usage_dict.items():
            devices_usage.append({
                'device_id': device_id,
                'total_minutes': 0,  # 不再统计时长
                'start_count': usage.get('yanghao_count', 0)
            })

        return {
            "today": today,
            "year_month": ym,
            "license": license,
            "machine_code": self.machine_code,
            "used_daily_yanghao": daily_usage['yanghao_count'],
            "used_daily_create": daily_usage['create_count'],
            "used_daily_export": daily_usage['export_count'],
            "used_daily_main_image": daily_usage['main_image_count'],
            "used_daily_cover_image": daily_usage['cover_image_count'],
            "used_daily_transfer": daily_usage['transfer_count'],
            "today_yanghao_device_id": daily_usage.get('yanghao_device_id'),
            "device_usage": device_usage_dict,
            "devices_usage": devices_usage,
            "registered_devices_count": self.get_registered_devices_count(),
        }
    
    def refresh_license(self) -> Tuple[bool, str]:
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
            permissions = license_data.get("permissions", {})

            # 从服务端套餐配置中获取配额
            package_config = self.package_config.get(package_type, {})

            # 优先使用协议中的 permissions 结构
            if permissions:
                parsed_permissions = self._parse_permissions_from_protocol(permissions)
                max_devices = parsed_permissions.get("max_devices", current.get("max_devices", 3))
                max_daily_yanghao = parsed_permissions.get("max_daily_yanghao", current.get("max_daily_yanghao", 9))
                max_daily_create = parsed_permissions.get("max_daily_create", current.get("max_daily_create", 15))
                max_daily_export = parsed_permissions.get("max_daily_export", current.get("max_daily_export", 30))
                max_daily_main_image = parsed_permissions.get("max_daily_main_image", current.get("max_daily_main_image", 15))
                max_daily_cover_image = parsed_permissions.get("max_daily_cover_image", current.get("max_daily_cover_image", 15))
                max_single_yanghao_minutes = parsed_permissions.get("max_single_yanghao_minutes", current.get("max_single_yanghao_minutes", 60))
                daily_yanghao_device_limit = parsed_permissions.get("daily_yanghao_device_limit", current.get("daily_yanghao_device_limit", False))
            else:
                # 使用服务端返回的或本地默认的配额（兼容旧版）
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



_license_manager_instance = None


def get_license_manager():
    """获取授权管理器单例"""
    global _license_manager_instance
    if _license_manager_instance is None:
        _license_manager_instance = LicenseManager()
    return _license_manager_instance


# ==================== 兼容旧版方法 ====================
def check_launch_permission(self) -> Tuple[bool, str]:
    """兼容旧版：检查启动权限"""
    license = self.get_current_license()
    if license.get("package_type") == "free":
        return False, "未激活，请先输入激活码"
    
    expire_date = license.get("expire_date")
    if expire_date:
        try:
            expire_dt = datetime.strptime(expire_date, "%Y-%m-%d")
            if datetime.now() > expire_dt:
                return False, "授权已过期"
        except:
            pass
    return True, "权限检查通过"

def check_daily_limit(self, device_id: str, additional_minutes: int = 0) -> Tuple[bool, str]:
    """兼容旧版：检查每日时长限制"""
    return True, "无时长限制"

def record_usage_start(self, device_id: str):
    """兼容旧版：记录使用开始"""
    self.on_start(device_id)

def record_usage_minutes(self, device_id: str, minutes: int):
    """兼容旧版：记录使用时长（新版不再统计时长）"""
    pass

def get_device_usage_today(self, device_id: str) -> Optional[Dict]:
    """兼容旧版：获取设备今日使用情况"""
    return None

def get_all_devices_usage_today(self):
    """兼容旧版：获取所有设备今日使用情况"""
    return []

def get_license_info(self) -> Optional[Dict]:
    """兼容旧版：获取授权信息"""
    return self.get_current_license()


# 添加兼容方法到 LicenseManager 类
LicenseManager.check_launch_permission = check_launch_permission
LicenseManager.check_daily_limit = check_daily_limit
LicenseManager.record_usage_start = record_usage_start
LicenseManager.record_usage_minutes = record_usage_minutes
LicenseManager.get_device_usage_today = get_device_usage_today
LicenseManager.get_all_devices_usage_today = get_all_devices_usage_today
LicenseManager.get_license_info = get_license_info
