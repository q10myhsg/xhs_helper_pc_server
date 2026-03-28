import sqlite3
import os
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DBManager:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "config/license.db"):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
    
    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"创建数据库目录: {db_dir}")
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                use_date TEXT NOT NULL,
                total_minutes INTEGER DEFAULT 0,
                start_count INTEGER DEFAULT 0,
                update_time TEXT NOT NULL,
                UNIQUE(device_id, use_date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_license (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activation_code TEXT UNIQUE NOT NULL,
                machine_code TEXT UNIQUE,
                package_type TEXT NOT NULL,
                expire_date TEXT NOT NULL,
                max_devices INTEGER NOT NULL,
                max_daily_minutes INTEGER NOT NULL,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                create_time TEXT NOT NULL,
                UNIQUE(device_id, keyword)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
    
    def save_user_license(self, activation_code: str, machine_code: str, 
                          package_type: str, expire_date: str, 
                          max_devices: int, max_daily_minutes: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO user_license 
                (activation_code, machine_code, package_type, expire_date, 
                 max_devices, max_daily_minutes, create_time, update_time, active)
                VALUES (?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT create_time FROM user_license WHERE activation_code = ?), ?), 
                        ?, 1)
            ''', (activation_code, machine_code, package_type, expire_date, 
                  max_devices, max_daily_minutes, activation_code, now, now))
            conn.commit()
            logger.info(f"已保存用户授权: {activation_code}")
            return True
        except Exception as e:
            logger.error(f"保存用户授权失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user_license(self) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM user_license WHERE active = 1 LIMIT 1')
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"获取用户授权失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_daily_usage(self, device_id: str, minutes: int = 0, increment_start: bool = False):
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now().isoformat()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO daily_usage (device_id, use_date, total_minutes, start_count, update_time)
                VALUES (?, ?, 0, 0, ?)
            ''', (device_id, today, now))
            
            if minutes > 0:
                cursor.execute('''
                    UPDATE daily_usage 
                    SET total_minutes = total_minutes + ?, update_time = ?
                    WHERE device_id = ? AND use_date = ?
                ''', (minutes, now, device_id, today))
            
            if increment_start:
                cursor.execute('''
                    UPDATE daily_usage 
                    SET start_count = start_count + 1, update_time = ?
                    WHERE device_id = ? AND use_date = ?
                ''', (now, device_id, today))
            
            conn.commit()
        except Exception as e:
            logger.error(f"更新每日使用统计失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_daily_usage(self, device_id: str) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            cursor.execute('''
                SELECT * FROM daily_usage 
                WHERE device_id = ? AND use_date = ?
            ''', (device_id, today))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"获取每日使用统计失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_all_devices_usage_today(self) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            cursor.execute('''
                SELECT * FROM daily_usage 
                WHERE use_date = ?
            ''', (today,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取今日所有设备使用统计失败: {e}")
            return []
        finally:
            conn.close()
    
    def save_keywords(self, device_id: str, keywords: List[str]) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute('DELETE FROM keywords WHERE device_id = ?', (device_id,))
            for keyword in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO keywords (device_id, keyword, create_time)
                    VALUES (?, ?, ?)
                ''', (device_id, keyword, now))
            conn.commit()
            logger.info(f"已保存设备 {device_id} 的关键词，共 {len(keywords)} 个")
            return True
        except Exception as e:
            logger.error(f"保存关键词失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_keywords(self, device_id: str) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT keyword FROM keywords WHERE device_id = ? ORDER BY id', (device_id,))
            rows = cursor.fetchall()
            return [row['keyword'] for row in rows]
        except Exception as e:
            logger.error(f"获取关键词失败: {e}")
            return []
        finally:
            conn.close()
    
    def delete_all_keywords(self, device_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM keywords WHERE device_id = ?', (device_id,))
            conn.commit()
            logger.info(f"已删除设备 {device_id} 的所有关键词")
            return True
        except Exception as e:
            logger.error(f"删除关键词失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
