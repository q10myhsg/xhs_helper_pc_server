#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xhs_helper_pc_server 商业化授权功能测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime, timedelta

print("=" * 80)
print("xhs_helper_pc_server 商业化授权功能测试")
print("=" * 80)

# 配置
API_BASE = "https://1259223433-0gnwuwcg9e.ap-beijing.tencentscf.com/v1"
API_KEY = "wenyang666"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

test_results = []

def log_test(test_name, passed, details=""):
    test_results.append({
        "name": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   {details}")

print("\n" + "=" * 60)
print("测试 1: 模块导入和初始化")
print("=" * 60)

try:
    from db_manager import DBManager
    from license_manager import LicenseManager
    from machine_code import get_machine_code
    
    db = DBManager()
    lm = LicenseManager(api_base_url=API_BASE, api_key=API_KEY)
    mc = get_machine_code()
    
    log_test("模块导入和初始化", True, f"机器码: {mc}")
except Exception as e:
    log_test("模块导入和初始化", False, str(e))

print("\n" + "=" * 60)
print("测试 2: 测试云端 API 连接")
print("=" * 60)

try:
    test_machine_code = "test-pc-server-" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    print(f"测试机器码: {test_machine_code}")
    log_test("云端 API 连接准备", True)
except Exception as e:
    log_test("云端 API 连接准备", False, str(e))

print("\n" + "=" * 60)
print("测试 3: 生成测试激活码")
print("=" * 60)

auth_code = None
try:
    generate_body = {
        "duration": 7,
        "count": 1,
        "package_type": "basic"
    }
    
    resp = requests.post(f"{API_BASE}/auth/generate", headers=headers, json=generate_body, timeout=10)
    print(f"生成激活码 - 状态码: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("status") == "success":
            auth_code = result["data"]["auth_codes"][0]
            log_test("生成测试激活码", True, f"激活码: {auth_code[:20]}...")
        else:
            log_test("生成测试激活码", False, f"状态: {result.get('status')}")
    else:
        log_test("生成测试激活码", False, f"HTTP {resp.status_code}")
except Exception as e:
    log_test("生成测试激活码", False, str(e))

print("\n" + "=" * 60)
print("测试 4: 验证激活码")
print("=" * 60)

if auth_code:
    try:
        verify_body = {
            "auth_code": auth_code,
            "machine_code": test_machine_code,
            "client_type": "pc-client",
            "plugin_version": "1.0.0"
        }
        
        resp2 = requests.post(f"{API_BASE}/auth/verify", headers=headers, json=verify_body, timeout=10)
        print(f"验证激活码 - 状态码: {resp2.status_code}")
        
        if resp2.status_code == 200:
            result2 = resp2.json()
            print(f"响应: {json.dumps(result2, indent=2, ensure_ascii=False)}")
            
            if result2.get("status") == "valid":
                log_test("验证激活码", True, 
                        f"套餐: {result2['data'].get('package_type')}, "
                        f"过期: {result2['data'].get('expiry_date')}")
            else:
                log_test("验证激活码", False, f"状态: {result2.get('status')}")
        else:
            log_test("验证激活码", False, f"HTTP {resp2.status_code}")
    except Exception as e:
        log_test("验证激活码", False, str(e))
else:
    log_test("验证激活码", False, "跳过，没有生成激活码")

print("\n" + "=" * 60)
print("测试 5: 测试 LicenseManager 的 verify_activation_code 方法")
print("=" * 60)

if auth_code:
    try:
        success, message, data = lm.verify_activation_code(auth_code)
        
        if success:
            log_test("LicenseManager 验证激活码", True, f"{message}")
        else:
            log_test("LicenseManager 验证激活码", False, f"{message}")
    except Exception as e:
        log_test("LicenseManager 验证激活码", False, str(e))
else:
    log_test("LicenseManager 验证激活码", False, "跳过，没有生成激活码")

print("\n" + "=" * 60)
print("测试 6: 测试数据库功能")
print("=" * 60)

try:
    from db_manager import DBManager
    db_test = DBManager(db_path="test_license.db")
    
    test_activation_code = "TEST_" + datetime.now().strftime("%Y%m%d%H%M%S")
    test_machine = "test-machine-001"
    test_package = "premium"
    test_expire = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    save_ok = db_test.save_user_license(
        test_activation_code, test_machine, test_package, 
        test_expire, 3, 300
    )
    
    if save_ok:
        license_info = db_test.get_user_license()
        if license_info and license_info["activation_code"] == test_activation_code:
            log_test("数据库保存和读取授权", True)
        else:
            log_test("数据库保存和读取授权", False, "读取的数据不匹配")
    else:
        log_test("数据库保存和读取授权", False, "保存失败")
    
    db_test.update_daily_usage("test-device-001", minutes=15, increment_start=True)
    usage = db_test.get_daily_usage("test-device-001")
    
    if usage and usage["total_minutes"] == 15 and usage["start_count"] == 1:
        log_test("数据库每日使用统计", True)
    else:
        log_test("数据库每日使用统计", False, f"得到: {usage}")
    
    if os.path.exists("test_license.db"):
        os.unlink("test_license.db")
        
except Exception as e:
    log_test("数据库功能测试", False, str(e))
    if os.path.exists("test_license.db"):
        try:
            os.unlink("test_license.db")
        except:
            pass

print("\n" + "=" * 60)
print("测试 7: 测试权限检查功能")
print("=" * 60)

try:
    allowed, msg = lm.check_launch_permission()
    log_test("权限检查功能", True, f"允许: {allowed}, 消息: {msg}")
except Exception as e:
    log_test("权限检查功能", False, str(e))

print("\n" + "=" * 80)
print("测试结果汇总")
print("=" * 80)

total_tests = len(test_results)
passed_tests = sum(1 for r in test_results if r["passed"])
failed_tests = total_tests - passed_tests

print(f"\n总计: {total_tests} 个测试")
print(f"通过: {passed_tests} 个 ✅")
print(f"失败: {failed_tests} 个 ❌")

if failed_tests == 0:
    print("\n🎉 所有测试通过！")
else:
    print("\n⚠️  部分测试失败，请检查：")
    for r in test_results:
        if not r["passed"]:
            print(f"  - {r['name']}: {r['details']}")

print("\n" + "=" * 80)

report_data = {
    "test_date": datetime.now().isoformat(),
    "total_tests": total_tests,
    "passed_tests": passed_tests,
    "failed_tests": failed_tests,
    "details": test_results
}

report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          "docs", "server", f"PC_SERVER_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)

print(f"\n测试报告已保存到: {report_path}")
