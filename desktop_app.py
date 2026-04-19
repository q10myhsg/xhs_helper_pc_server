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


def check_server_ready():
    """检查服务器是否就绪"""
    import urllib.request
    try:
        with urllib.request.urlopen('http://localhost:5002', timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


class Api:
    """PyWebview API 类，暴露给前端的方法"""
    
    def open_file_dialog(self):
        """打开文件选择对话框，支持多选PDF文件"""
        try:
            import webview
            # 使用PyWebview的文件选择对话框
            file_paths = webview.windows[0].create_file_dialog(
                dialog_type=webview.FOLDER_DIALOG | webview.OPEN_DIALOG,
                directory='',
                allow_multiple=True,
                save_filename='',
                file_types=('PDF文件 (*.pdf)', '所有文件 (*.*)')
            )
            
            if file_paths:
                # 过滤出PDF文件
                pdf_paths = [p for p in file_paths if p.lower().endswith('.pdf')]
                return {
                    'success': True,
                    'file_paths': pdf_paths
                }
            else:
                return {
                    'success': False,
                    'message': '未选择文件'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def open_pdf_file_dialog(self):
        """专门打开PDF文件选择对话框"""
        try:
            import webview
            # 使用PyWebview的文件选择对话框，专门选择PDF文件
            file_paths = webview.windows[0].create_file_dialog(
                dialog_type=webview.OPEN_DIALOG,
                directory='',
                allow_multiple=True,
                save_filename='',
                file_types=('PDF文件 (*.pdf)', '所有文件 (*.*)')
            )
            
            if file_paths:
                return {
                    'success': True,
                    'file_paths': file_paths
                }
            else:
                return {
                    'success': False,
                    'message': '未选择文件'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def open_directory_dialog(self):
        """打开目录选择对话框"""
        try:
            import webview
            # 使用PyWebview的文件夹选择对话框
            dir_path = webview.windows[0].create_file_dialog(
                dialog_type=webview.FOLDER_DIALOG,
                directory='',
                allow_multiple=False,
                save_filename=''
            )
            
            if dir_path and len(dir_path) > 0:
                return {
                    'success': True,
                    'directory': dir_path[0]
                }
            else:
                return {
                    'success': False,
                    'message': '未选择目录'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def open_image_file_dialog(self):
        """打开图片文件选择对话框，用于选择水印/页眉/页脚图片"""
        try:
            import webview
            # 使用PyWebview的文件选择对话框，专门选择图片文件
            file_paths = webview.windows[0].create_file_dialog(
                dialog_type=webview.OPEN_DIALOG,
                directory='',
                allow_multiple=False,
                save_filename='',
                file_types=('图片文件 (*.png;*.jpg;*.jpeg;*.gif;*.bmp)', '所有文件 (*.*)')
            )
            
            if file_paths and len(file_paths) > 0:
                return {
                    'success': True,
                    'file_path': file_paths[0]
                }
            else:
                return {
                    'success': False,
                    'message': '未选择文件'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }


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
    
    # 启动 PyWebview 窗口，先显示 loading 页面
    logger.info("正在启动桌面窗口...")
    
    # 创建一个临时的 loading HTML
    loading_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>正在加载...</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .loading-container {
                text-align: center;
                padding: 40px;
            }
            .spinner {
                width: 60px;
                height: 60px;
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            h1 {
                font-size: 28px;
                margin-bottom: 15px;
                font-weight: 600;
            }
            p {
                font-size: 16px;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="loading-container">
            <div class="spinner"></div>
            <h1>🚀 正在启动小红书助手</h1>
            <p>服务器正在准备中，请稍候...</p>
        </div>
    </body>
    </html>
    """
    
    # 创建API实例
    api = Api()
    
    # 创建窗口，先显示 loading 页面
    window = webview.create_window(
        title='小红书助手',
        html=loading_html,
        js_api=api,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # 在后台线程中启动 Flask 服务器
    logger.info("正在启动后台服务器...")
    server_thread = threading.Thread(target=start_flask_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动，同时显示 loading 页面
    def wait_and_load():
        import time
        logger.info("等待服务器就绪...")
        
        # 等待服务器准备好
        max_wait = 30  # 最多等待30秒
        for i in range(max_wait):
            if check_server_ready():
                logger.info(f"服务器在第 {i+1} 秒就绪！")
                break
            time.sleep(1)
        
        # 跳转到主应用
        logger.info("加载主应用页面...")
        window.load_url('http://localhost:5002')
    
    # 在另一个线程中等待服务器并加载主页面
    wait_thread = threading.Thread(target=wait_and_load, daemon=True)
    wait_thread.start()
    
    # 启动 PyWebview 事件循环
    webview.start()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
