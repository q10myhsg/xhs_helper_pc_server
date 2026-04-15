#!/usr/bin/env python3
import requests
import json

# 激活信息
activation_code = "83a458221598966803c2c5e38b02600f"
machine_code = "1_QWbAdLRkL3mif39sNeDF"

# 正确的 API 地址和配置
api_url = "https://1259223433-0gnwuwcg9e.ap-beijing.tencentscf.com/auth/verify"
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

# 打印请求信息
print("="*60)
print("激活请求信息:")
print(f"API 地址: {api_url}")
print(f"激活码: {activation_code}")
print(f"机器码: {machine_code}")
print(f"请求头: {json.dumps(headers, indent=2)}")
print(f"请求数据: {json.dumps(request_data, indent=2)}")
print("="*60)
print()

try:
    # 发送请求
    response = requests.post(api_url, json=request_data, headers=headers, timeout=10)
    
    # 打印响应信息
    print("响应结果:")
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"响应数据: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"响应文本: {response.text}")
    
    print("="*60)
    
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    print("="*60)
