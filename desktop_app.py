#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面应用启动器
功能：启动 Flask 后台服务 + PyWebview 桌面窗口
"""

import os
import sys
import threading
import logging
import webview
from waitress import serve

# 修复 uiautomator2 资源路径问题
try:
    import uiautomator2_patch
except ImportError:
    pass


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
    )


def start_flask_server():
    """在后台线程中启动 Flask 服务器（使用 Waitress 生产服务器）"""
    try:
        # 确保配置文件存在
        os.makedirs("config", exist_ok=True)
        if not os.path.exists("config/config.json"):
            import json
            with open("config/config.json", "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
        
        # 导入 app
        from app import app
        
        logger = logging.getLogger(__name__)
        logger.info("启动 Flask 生产服务器 (Waitress)...")
        
        # 使用 Waitress 启动服务器
        serve(app, host='0.0.0.0', port=5002, threads=4)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"启动 Flask 服务器失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 尝试导入环境检查模块
        from env_checker import EnvChecker
        from env_installer import EnvInstaller
        
        checker = EnvChecker()
        results = checker.check_all()
        
        # 检查是否有缺失的核心依赖
        missing = checker.get_missing_dependencies()
        
        if missing:
            logger.warning("检测到缺失的依赖项！")
            print("="*60)
            print("检测到缺失的依赖项！")
            print(checker.get_summary())
            print("="*60)
            
            # 尝试启动环境配置 GUI
            try:
                import tkinter as tk
                from env_setup_gui import EnvSetupApp
                
                print("\n正在启动环境配置工具...")
                root = tk.Tk()
                app = EnvSetupApp(root)
                root.mainloop()
                
            except ImportError:
                print("\n环境配置工具不可用，请手动安装以下依赖：")
                for dep in missing:
                    print(f"  - {dep}")
                print("\n或运行: python env_setup_gui.py")
                return 1
        else:
            logger.info("所有依赖项已满足")
            print(checker.get_summary())
        
        # 将我们的工具目录添加到 PATH
        installer = EnvInstaller()
        bin_dir = installer.get_bin_dir()
        if bin_dir and bin_dir not in os.environ['PATH']:
            os.environ['PATH'] = bin_dir + os.pathsep + os.environ['PATH']
            
    except ImportError as e:
        logger.warning(f"环境检查模块不可用: {e}")
        print("环境检查模块不可用，直接启动...")
    except Exception as e:
        logger.error(f"启动过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 在后台线程中启动 Flask 服务器
    logger.info("正在启动后台服务器...")
    server_thread = threading.Thread(target=start_flask_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    import time
    time.sleep(2)
    
    # 启动 PyWebview 窗口
    logger.info("正在启动桌面窗口...")
    
    # 创建窗口
    window = webview.create_window(
        title='小红书助手',
        url='http://localhost:5002',
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # 启动 PyWebview 事件循环
    webview.start()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
