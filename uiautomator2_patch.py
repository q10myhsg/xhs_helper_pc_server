#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 uiautomator2 在 PyInstaller 打包环境下的资源路径问题
简单直接的方法：在 uiautomator2 导入前，设置好资源路径
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
    
    # 先导入 uiautomator2
    import uiautomator2
    
    # 获取 uiautomator2 的安装目录
    uiautomator2_dir = os.path.dirname(uiautomator2.__file__)
    print(f"[uiautomator2_patch] uiautomator2 安装目录: {uiautomator2_dir}")
    
    # 预期的 assets 路径
    expected_assets_path = os.path.join(uiautomator2_dir, 'assets')
    print(f"[uiautomator2_patch] 预期的 assets 路径: {expected_assets_path}")
    
    # 检查是否已经有我们的标记文件
    marker_file = os.path.join(expected_assets_path, '.xhs_helper_patched')
    
    if os.path.exists(marker_file):
        print(f"[uiautomator2_patch] Assets 已经存在且已标记，跳过")
        return
    
    # 尝试复制 assets 目录
    try:
        import shutil
        
        # 如果 expected_assets_path 已存在，先删除
        if os.path.exists(expected_assets_path):
            if os.path.islink(expected_assets_path):
                os.unlink(expected_assets_path)
            else:
                shutil.rmtree(expected_assets_path)
        
        # 复制 assets 目录
        shutil.copytree(assets_in_meipass, expected_assets_path)
        
        # 创建标记文件
        with open(marker_file, 'w') as f:
            f.write('patched')
        
        print(f"[uiautomator2_patch] 成功复制 assets 到: {expected_assets_path}")
        print(f"[uiautomator2_patch] Assets 内容: {os.listdir(expected_assets_path)}")
    
    except Exception as e:
        print(f"[uiautomator2_patch] 复制 assets 失败: {e}")
        import traceback
        traceback.print_exc()


# 自动应用补丁
patch_uiautomator2()
