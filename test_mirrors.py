#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ADB 镜像源是否可访问
"""

import urllib.request
import urllib.error
import time

# 镜像源列表
mirrors = [
    ('腾讯云', 'https://mirrors.cloud.tencent.com/AndroidSDK/'),
    ('清华大学', 'https://mirrors.tuna.tsinghua.edu.cn/AndroidSDK/'),
    ('腾讯 Bugly', 'http://android-mirror.bugly.qq.com:8080/android/repository/'),
    ('Google 官方', 'https://dl.google.com/android/repository/'),
]

test_file = 'platform-tools-latest-windows.zip'

print('=' * 60)
print('测试 ADB 镜像源访问性')
print('=' * 60)
print()

for name, url in mirrors:
    print(f'测试 {name}...')
    full_url = url + test_file
    
    try:
        start_time = time.time()
        
        # 只请求头部，不下载整个文件
        req = urllib.request.Request(full_url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            elapsed = time.time() - start_time
            status = response.status
            print(f'  ✓ 可访问 (状态码: {status}, 耗时: {elapsed:.2f}s)')
            
            # 尝试获取文件大小
            content_length = response.getheader('Content-Length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                print(f'  文件大小: {size_mb:.2f} MB')
                
    except urllib.error.HTTPError as e:
        print(f'  ✗ HTTP 错误: {e.code} - {e.reason}')
    except urllib.error.URLError as e:
        print(f'  ✗ 连接失败: {e.reason}')
    except Exception as e:
        print(f'  ✗ 错误: {str(e)}')
    
    print()

print('=' * 60)
print('测试完成')
print('=' * 60)
