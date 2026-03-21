#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试给定的激活码
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from license_manager import LicenseManager

print("=" * 80)
print("测试激活码验证")
print("=" * 80)

auth_code = "30_L9V3EvuHAMuMKMzr19de"

print(f"\n激活码: {auth_code}")

print("\n正在初始化 LicenseManager...")
lm = LicenseManager()

print("\n正在验证激活码...")
success, message, data = lm.verify_activation_code(auth_code)

print("\n" + "=" * 80)
print("验证结果")
print("=" * 80)

if success:
    print(f"✅ 验证成功！")
    print(f"消息: {message}")
    if data:
        print(f"\n授权详情:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    
    print("\n从数据库读取授权信息:")
    license_info = lm.get_license_info()
    if license_info:
        for key, value in license_info.items():
            print(f"  {key}: {value}")
    
    print("\n检查启动权限:")
    allowed, msg = lm.check_launch_permission()
    print(f"  允许启动: {allowed}")
    print(f"  消息: {msg}")
    
else:
    print(f"❌ 验证失败！")
    print(f"消息: {message}")

print("\n" + "=" * 80)
