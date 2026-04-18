#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动器脚本
功能：先运行环境检查，再启动主应用
"""

import os
import sys
import subprocess


def main():
    try:
        # 尝试导入环境检查模块
        from env_checker import EnvChecker
        from env_installer import EnvInstaller
        
        checker = EnvChecker()
        results = checker.check_all()
        
        # 检查是否有缺失的核心依赖
        missing = checker.get_missing_dependencies()
        
        if missing:
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
            # 所有依赖都满足，直接启动主应用
            print(checker.get_summary())
            print("\n所有依赖项已满足，正在启动主应用...")
            
            # 将我们的工具目录添加到 PATH
            installer = EnvInstaller()
            bin_dir = installer.get_bin_dir()
            if bin_dir and bin_dir not in os.environ['PATH']:
                os.environ['PATH'] = bin_dir + os.pathsep + os.environ['PATH']
            
            # 启动主应用
            return launch_app()
            
    except ImportError as e:
        print(f"环境检查模块不可用: {e}")
        print("直接启动主应用...")
        return launch_app()
    except Exception as e:
        print(f"启动过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return launch_app()


def launch_app():
    """启动主应用"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, 'app.py')
    
    if not os.path.exists(app_path):
        print(f"错误: 找不到 app.py: {app_path}")
        return 1
    
    print(f"启动主应用: {app_path}")
    
    # 使用当前 Python 解释器启动 app.py
    try:
        subprocess.run([sys.executable, app_path])
        return 0
    except KeyboardInterrupt:
        print("\n应用已停止")
        return 0
    except Exception as e:
        print(f"启动主应用失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
