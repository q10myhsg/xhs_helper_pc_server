#!/usr/bin/env python3
"""
清空今天的养号记录脚本
用于调试和测试
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'xhs_helper_pc_server'))

from db_manager import DBManager


def clear_today_usage(device_id=None):
    """
    清空今天的养号记录
    :param device_id: 设备ID，为None时清空所有设备的记录
    """
    db_manager = DBManager()
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('DELETE FROM daily_usage WHERE device_id = ? AND use_date = ?', (device_id, today))
            print(f"已清空设备 {device_id} 今天的养号记录")
        else:
            cursor.execute('DELETE FROM daily_usage WHERE use_date = ?', (today,))
            print("已清空所有设备今天的养号记录")
        
        conn.commit()
        print("操作成功！")
    except Exception as e:
        print(f"操作失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='清空今天的养号记录')
    parser.add_argument('--device', '-d', help='设备ID，不指定则清空所有设备')
    args = parser.parse_args()
    
    clear_today_usage(args.device)
