#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置 GUI 工具
功能：图形化界面让用户选择安装组件
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

try:
    from env_checker import EnvChecker
    from env_installer import EnvInstaller
    from venv_manager import VenvManager
except ImportError:
    pass


class EnvSetupApp:
    """环境配置应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("xhs_helper 环境配置工具")
        self.root.geometry("700x600")
        
        # 初始化组件
        self.checker = None
        self.installer = None
        self.venv_manager = None
        
        try:
            self.checker = EnvChecker()
            self.installer = EnvInstaller()
            self.venv_manager = VenvManager()
        except NameError:
            pass
        
        self.results = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="xhs_helper 环境配置工具",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 系统信息
        self.system_info = tk.StringVar()
        if self.checker:
            self.system_info.set(
                f"系统: {self.checker.system} {self.checker.architecture}"
            )
        else:
            self.system_info.set("系统: 未知")
        
        system_label = ttk.Label(main_frame, textvariable=self.system_info)
        system_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        # 检查状态按钮
        check_button = ttk.Button(
            main_frame,
            text="检查环境",
            command=self._check_environment
        )
        check_button.grid(row=2, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)
        
        # 组件选择框架
        components_frame = ttk.LabelFrame(main_frame, text="可选组件", padding="10")
        components_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15))
        components_frame.columnconfigure(1, weight=1)
        
        # 组件复选框
        self.adb_var = tk.BooleanVar(value=True)
        self.poppler_var = tk.BooleanVar(value=True)
        self.venv_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(
            components_frame,
            text="ADB (Android 调试桥)",
            variable=self.adb_var
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(
            components_frame,
            text="Poppler (PDF 处理工具)",
            variable=self.poppler_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(
            components_frame,
            text="创建 Python 虚拟环境",
            variable=self.venv_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 安装按钮
        install_button = ttk.Button(
            main_frame,
            text="安装选中组件",
            command=self._install_components
        )
        install_button.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky=tk.EW)
        
        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW+tk.NS, pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=15,
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky=tk.EW+tk.NS)
        
        # 启动主应用按钮
        self.start_button = ttk.Button(
            main_frame,
            text="启动 xhs_helper",
            command=self._start_app,
            state='disabled'
        )
        self.start_button.grid(row=6, column=0, columnspan=2, pady=(10, 0), sticky=tk.EW)
        
        # 初始检查
        self._log("欢迎使用 xhs_helper 环境配置工具！")
        self._log("点击 '检查环境' 开始检查您的系统环境")
    
    def _log(self, message: str):
        """添加日志消息"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
    
    def _check_environment(self):
        """检查环境"""
        if not self.checker:
            messagebox.showerror("错误", "环境检查模块不可用")
            return
        
        self._log("\n" + "="*50)
        self._log("开始检查环境...")
        
        def check_thread():
            try:
                results = self.checker.check_all()
                self.results = results
                
                self._log(self.checker.get_summary())
                
                missing = self.checker.get_missing_dependencies()
                if missing:
                    self._log(f"\n缺失的核心依赖项: {', '.join(missing)}")
                    self._log("请选择需要安装的组件并点击 '安装选中组件'")
                else:
                    self._log("\n✓ 所有核心依赖项已满足！")
                    self.start_button.config(state='normal')
            except Exception as e:
                self._log(f"检查环境时出错: {str(e)}")
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def _install_components(self):
        """安装选中的组件"""
        if not self.installer:
            messagebox.showerror("错误", "环境安装模块不可用")
            return
        
        components = []
        if self.adb_var.get():
            components.append('adb')
        if self.poppler_var.get():
            components.append('poppler')
        
        if not components and not self.venv_var.get():
            messagebox.showwarning("警告", "请至少选择一个组件")
            return
        
        self._log("\n" + "="*50)
        self._log("开始安装组件...")
        
        def install_thread():
            try:
                if components:
                    self._log(f"将要安装的组件: {', '.join(components)}")
                    
                    def progress_callback(component, status, message):
                        self._log(f"[{status.upper()}] {component}: {message}")
                    
                    results = self.installer.install_all(components, progress_callback)
                    
                    success_count = sum(1 for r in results.values() if r['success'])
                    self._log(f"\n安装完成: {success_count}/{len(results)} 成功")
                    
                    for name, result in results.items():
                        if result['success']:
                            self._log(f"✓ {name}: {result['message']}")
                        else:
                            self._log(f"✗ {name}: {result['message']}")
                
                if self.venv_var.get() and self.venv_manager:
                    self._log("\n创建 Python 虚拟环境...")
                    venv_result = self.venv_manager.create_venv()
                    if venv_result['success']:
                        self._log(f"✓ {venv_result['message']}")
                    else:
                        self._log(f"✗ {venv_result['message']}")
                
                self._log("\n安装完成！请重新检查环境")
                self.start_button.config(state='normal')
                
            except Exception as e:
                self._log(f"安装时出错: {str(e)}")
                import traceback
                self._log(traceback.format_exc())
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def _start_app(self):
        """启动主应用"""
        self._log("\n启动 xhs_helper...")
        try:
            import subprocess
            
            # 首先将安装目录添加到 PATH
            if self.installer:
                bin_dir = self.installer.get_bin_dir()
                if bin_dir and bin_dir not in os.environ['PATH']:
                    os.environ['PATH'] = bin_dir + os.pathsep + os.environ['PATH']
            
            self._log("正在启动主应用程序...")
            self.root.destroy()
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            app_path = os.path.join(script_dir, 'app.py')
            
            if os.path.exists(app_path):
                subprocess.Popen([sys.executable, app_path])
            else:
                messagebox.showerror("错误", f"找不到 app.py: {app_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动应用时出错: {str(e)}")


def main():
    root = tk.Tk()
    app = EnvSetupApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
