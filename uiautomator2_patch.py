#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 uiautomator2 在 PyInstaller 打包环境下的资源路径问题
超级直接的方法 - monkey patch Path 类！
"""

import os
import sys


def patch_uiautomator2():
    """
    修复 uiautomator2 的资源路径
    """
    # 判断是否在 PyInstaller 打包环境中
    if not hasattr(sys, '_MEIPASS'):
        print("[uiautomator2_patch] 不在 PyInstaller 打包环境中，跳过补丁")
        return
    
    meipass_path = sys._MEIPASS
    print(f"[uiautomator2_patch] 检测到 PyInstaller 打包环境")
    print(f"[uiautomator2_patch] _MEIPASS 路径: {meipass_path}")
    
    # 检查 _MEIPASS 中是否有 uiautomator2/assets
    assets_in_meipass = os.path.join(meipass_path, 'uiautomator2', 'assets')
    
    if not os.path.exists(assets_in_meipass):
        print(f"[uiautomator2_patch] 警告: 在 _MEIPASS 中未找到 uiautomator2/assets 目录")
        if os.path.exists(meipass_path):
            print(f"[uiautomator2_patch] _MEIPASS 内容: {os.listdir(meipass_path)}")
        return
    
    print(f"[uiautomator2_patch] Assets 目录存在于 _MEIPASS")
    print(f"[uiautomator2_patch] Assets 目录内容: {os.listdir(assets_in_meipass)}")
    
    # 好的，现在我们用最直接的方法 - monkey patch pathlib.Path！
    try:
        from pathlib import Path
        import inspect
        
        # 保存原始的 Path.__new__
        original_path_new = Path.__new__
        
        def patched_path_new(cls, *args, **kwargs):
            """
            补丁版的 Path 构造函数
            """
            result = original_path_new(cls, *args, **kwargs)
            
            # 检查是否是 uiautomator2 在调用
            stack = inspect.stack()
            
            for frame_info in stack:
                # 检查是否在 uiautomator2/core.py 中
                if 'core.py' in frame_info.filename and 'uiautomator2' in frame_info.filename:
                    # 检查是否在找 assets
                    if len(args) > 0:
                        arg_str = str(args[0])
                        if '__file__' in arg_str:
                            # 哦，我们找到了！这是 Path(__file__)
                            # 返回我们的 assets 目录的父目录
                            print(f"[uiautomator2_patch] 检测到 Path(__file__) 调用，返回我们的路径")
                            return Path(meipass_path) / 'uiautomator2'
            
            return result
        
        # 应用补丁！
        Path.__new__ = patched_path_new
        print(f"[uiautomator2_patch] 成功 monkey patch pathlib.Path！")
        
    except Exception as e:
        print(f"[uiautomator2_patch] patch Path 失败: {e}")
        import traceback
        traceback.print_exc()


# 立即应用补丁
patch_uiautomator2()
