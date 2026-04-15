#!/usr/bin/env python3
import requests
import json

# 正确的激活信息
activation_code = "1_QWbAdLRkL3mif39sNeDF"
machine_code = "83a458221598966803c2c5e38b02600f"

# 正确的 API 地址
api_url = "https://1259223433-ip1qx1uc34.ap-beijing.tencentscf.com/auth/verify"
headers = {
    "X-API-Key": "wenyang666",
    "Content-Type": "application/json",
}

# 准备请求数据
request_data = {
    "auth_code": activation_code,
    "machine_code": machine_code,
    "client_type": "pc-client",
    "plugin_version": "1.0.0",
}

print("="*80)
print("小红书助手 - 激活请求")
print("="*80)
print()

# 打印请求信息
print("请求信息:")
print(f"API 地址: {api_url}")
print(f"激活码: {activation_code}")
print(f"机器码: {machine_code}")
print()

# 发送请求
try:
    response = requests.post(api_url, json=request_data, headers=headers, timeout=10)
    
    # 打印响应信息
    print("响应结果:")
    print(f"状态码: {response.status_code}")
    print(f"状态: 成功 ✅")
    print()
    
    response_data = response.json()
    print("详细信息:")
    print(f"消息: {response_data['message']}")
    print(f"套餐类型: {response_data['data']['package_type']}")
    print(f"激活日期: {response_data['data']['activated_date']}")
    print(f"过期日期: {response_data['data']['expiry_date']}")
    print()
    
    print("="*80)
    print("激活成功！🎉")
    print("="*80)
    
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    print("="*80)
