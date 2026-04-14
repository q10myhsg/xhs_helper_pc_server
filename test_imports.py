#!/usr/bin/env python3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

print("="*60)
print("  测试模块导入")
print("="*60)
print()

modules = [
    'flask',
    'werkzeug',
    'uiautomator2',
    'PIL',
    'bs4',
    'lxml',
    'xhs_nurturing',
    'xhs_nurturing.nurturing_manager',
    'xhs_nurturing.config_manager',
    'xhs_nurturing.device_manager',
    'xhs_nurturing.interaction_manager',
    'xhs_nurturing.browse_manager',
    'xhs_nurturing.utils',
    'create_notes',
    'create_notes.xhs_parser',
    'license_manager',
    'machine_code',
    'pdf_converter',
    'file_transfer',
    'config_manager',
    'db_manager',
    'utils',
]

success = 0
failed = 0

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
        success += 1
    except Exception as e:
        print(f"✗ {module} - 错误: {e}")
        failed += 1

print()
print("="*60)
print(f"  结果: {success} 成功, {failed} 失败")
print("="*60)
