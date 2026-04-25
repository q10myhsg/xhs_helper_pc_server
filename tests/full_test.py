
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from license_manager import get_license_manager

print("=" * 60)
print("PC 客户端授权管理和使用统计功能测试")
print("=" * 60)

print("\n[1] 初始化 LicenseManager...")
lm = get_license_manager()
print("✅ LicenseManager 初始化成功！")

print("\n[2] 测试获取当前授权信息...")
license_info = lm.get_current_license()
print("✅ 获取授权信息成功：")
print(f"   - 套餐类型：{license_info['package_type']}")
print(f"   - 每日养号次数：{license_info['max_daily_yanghao']}")
print(f"   - 每日创作次数：{license_info['max_daily_create']}")
print(f"   - 每日导出次数：{license_info['max_daily_export']}")

print("\n[3] 测试获取使用统计信息...")
usage_stats = lm.get_usage_stats()
print("✅ 获取使用统计成功：")
print(f"   - 今日日期：{usage_stats['today']}")
print(f"   - 今日已使用养号次数：{usage_stats['used_daily_yanghao']}")
print(f"   - 今日已使用创作次数：{usage_stats['used_daily_create']}")

print("\n[4] 测试配额检查功能...")
test_device_id = "test-device-001"
can_start, message, actual_duration = lm.check_can_start(test_device_id, 30)
print("✅ 配额检查成功：")
print(f"   - 是否可以启动：{can_start}")
print(f"   - 提示信息：{message}")
print(f"   - 实际可以运行时长：{actual_duration}分钟")

print("\n" + "=" * 60)
print("✅ 所有功能测试完成！")
print("=" * 60)
