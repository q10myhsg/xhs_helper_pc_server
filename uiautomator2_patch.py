#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 uiautomator2 在 PyInstaller 打包环境下的资源路径问题
"""

import os
import sys


def patch_uiautomator2():
    """
    修复 uiautomator2 的资源路径，使其在 PyInstaller 打包环境下能正常工作
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
    
    # 现在导入 uiautomator2 并修改它的 __file__ 属性所在的目录
    import uiautomator2
    import uiautomator2.core
    
    # 获取 uiautomator2.core 的原始路径
    original_core_path = uiautomator2.core.__file__
    print(f"[uiautomator2_patch] 原始 core.py 路径: {original_core_path}")
    
    # 关键思路：我们需要让 Path(__file__).parent / "assets" 能找到我们的 assets
    # 方法：创建一个临时的 core.py 文件，放在有 assets 的目录下，或者直接 monkey patch
    
    # 方法 1：Monkey patch Path(__file__) 的行为
    # 我们可以 monkey patch uiautomator2.core 中的 Path 类
    
    try:
        from pathlib import Path
        
        # 保存原始的 Path.__new__ 方法
        original_path_new = Path.__new__
        
        def patched_path_new(cls, *args, **kwargs):
            """
            补丁版的 Path 构造函数
            当检测到 uiautomator2/core.py 在查找 assets 时，返回正确的路径
            """
            result = original_path_new(cls, *args, **kwargs)
            
            # 检查是否是 uiautomator2/core.py 在查找 assets
            # 检查调用栈
            import inspect
            stack = inspect.stack()
            
            for frame_info in stack:
                if 'core.py' in frame_info.filename and 'uiautomator2' in frame_info.filename:
                    # 看起来是 uiautomator2/core.py 在调用
                    # 检查是否在找 assets 目录
                    if len(args) > 0 and 'assets' in str(args[0]):
                        print(f"[uiautomator2_patch] 检测到 assets 查找请求: {args}")
                        # 返回我们的 assets 路径
                        return Path(assets_in_meipass)
            
            return result
        
        # 这个方法太复杂，换一个更直接的
        
    except Exception as e:
        print(f"[uiautomator2_patch] Path 补丁失败: {e}")
    
    # 方法 2：更简单直接 - 复制 assets 到 uiautomator2 包所在的位置
    original_uiautomator2_dir = os.path.dirname(original_core_path)
    expected_assets_path = os.path.join(original_uiautomator2_dir, 'assets')
    
    print(f"[uiautomator2_patch] 期望的 assets 路径: {expected_assets_path}")
    
    try:
        import shutil
        
        # 如果期望的 assets 路径存在且是我们复制的，跳过
        if os.path.exists(expected_assets_path):
            marker_file = os.path.join(expected_assets_path, '.xhs_helper_patched')
            if os.path.exists(marker_file):
                print(f"[uiautomator2_patch] Assets 已经存在且已标记，跳过")
                return
            
            # 备份或删除现有的 assets
            if os.path.islink(expected_assets_path):
                os.unlink(expected_assets_path)
            else:
                shutil.rmtree(expected_assets_path)
        
        # 复制 assets 目录
        shutil.copytree(assets_in_meipass, expected_assets_path)
        
        # 创建标记文件
        with open(os.path.join(expected_assets_path, '.xhs_helper_patched'), 'w') as f:
            f.write('patched')
        
        print(f"[uiautomator2_patch] 已成功复制 assets 到: {expected_assets_path}")
        print(f"[uiautomator2_patch] Assets 内容: {os.listdir(expected_assets_path)}")
    
    except Exception as e:
        print(f"[uiautomator2_patch] 复制 assets 失败: {e}")
        import traceback
        traceback.print_exc()


# 自动应用补丁
patch_uiautomator2()
