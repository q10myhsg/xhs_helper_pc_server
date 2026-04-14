#!/usr/bin/env python3
import os
import sys
import webbrowser
import threading
import time

def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("="*60)
    print("  小红书助手 - 正在启动...")
    print("="*60)
    print()
    
    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 导入并运行 Flask 应用
    from app import app
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n服务已停止")
        sys.exit(0)
