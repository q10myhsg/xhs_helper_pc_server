#!/usr/bin/env python3
"""
交叉编译脚本：在 macOS 上同时打包 macOS 和 Windows 版本

需要先安装：
1. PyInstaller
2. Wine (用于 Windows 打包)
3. Windows 版本的 Python 和 PyInstaller
"""

import os
import sys
import shutil
import subprocess
import platform
from datetime import datetime

# 配置
APP_NAME = "xhs_helper"
VERSION = "1.0.0"
RELEASE_DIR = "release"

# 需要包含的文件和目录
INCLUDE_FILES = [
    'templates',
    'static',
    'config',
    'resources',
    'create_notes',
    'xhs_nurturing',
]

# 需要隐藏导入的模块
HIDDEN_IMPORTS = [
    'flask',
    'werkzeug',
    'uiautomator2',
    'PIL',
    'bs4',
    'lxml',
    'xhs_nurturing',
    'create_notes',
    'license_manager',
    'machine_code',
    'pdf_converter',
    'file_transfer',
    'config_manager',
    'db_manager',
    'utils',
]

# 需要排除的模块
EXCLUDE_MODULES = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'sklearn',
    'skimage',
    'scikit-image',
    'imageio',
    'tkinter',
    'IPython',
    'jupyter',
    'notebook',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'traitlets',
    'pytest',
    'unittest',
]

def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    print(f"执行: {' '.join(cmd[:10])}...")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode

def build_macos():
    """打包 macOS 版本"""
    print("\n[1/2] 打包 macOS 版本...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--name', APP_NAME,
        '--onefile',
        '--console',
        '--noupx',
    ]
    
    # 添加文件
    for file in INCLUDE_FILES:
        cmd.extend(['--add-data', f'{file}:{file}'])
    
    # 添加隐藏导入
    for imp in HIDDEN_IMPORTS:
        cmd.extend(['--hidden-import', imp])
    
    # 排除模块
    for mod in EXCLUDE_MODULES:
        cmd.extend(['--exclude-module', mod])
    
    # 添加入口文件
    cmd.append('app.py')
    
    result = run_cmd(cmd)
    if result != 0:
        print(f"macOS 打包失败，返回码: {result}")
        return False
    
    # 创建发布包
    os.makedirs(RELEASE_DIR, exist_ok=True)
    
    # 复制可执行文件
    exe_path = f'dist/{APP_NAME}'
    if not os.path.exists(exe_path):
        print(f"找不到可执行文件: {exe_path}")
        return False
    
    # 创建版本目录
    version_dir = f"{APP_NAME}_v{VERSION}_macos_{platform.machine().lower()}"
    version_path = os.path.join(RELEASE_DIR, version_dir)
    os.makedirs(version_path, exist_ok=True)
    
    # 复制可执行文件
    shutil.copy(exe_path, version_path)
    
    # 创建 README
    create_readme(version_path, "macOS")
    
    # 创建压缩包
    create_zip(version_path, version_dir)
    
    print(f"macOS 版本打包完成: {version_dir}")
    return True

def build_windows():
    """打包 Windows 版本（使用 Wine）"""
    print("\n[2/2] 打包 Windows 版本...")
    
    # 检查 Wine 是否安装
    if not shutil.which('wine'):
        print("错误: 未安装 Wine，请先安装 Wine")
        print("安装命令: brew install --cask wine-stable")
        return False
    
    # 检查 Windows Python 是否安装
    if not os.path.exists(os.path.expanduser('~/.wine/drive_c/Python311/python.exe')):
        print("错误: 未安装 Windows 版本的 Python")
        print("请下载 Windows 版本的 Python 并通过 Wine 安装")
        return False
    
    # 复制文件到 Wine 目录
    wine_dir = os.path.expanduser('~/.wine/drive_c/xhs_helper')
    if os.path.exists(wine_dir):
        shutil.rmtree(wine_dir)
    
    # 创建 Wine 目录
    os.makedirs(wine_dir)
    
    # 复制项目文件
    for file in INCLUDE_FILES:
        if os.path.exists(file):
            shutil.copytree(file, os.path.join(wine_dir, file))
    
    # 复制 Python 文件
    python_files = [
        'app.py',
        'license_manager.py',
        'machine_code.py',
        'pdf_converter.py',
        'file_transfer.py',
        'config_manager.py',
        'db_manager.py',
        'utils.py',
        'requirements.txt',
    ]
    
    for file in python_files:
        if os.path.exists(file):
            shutil.copy(file, wine_dir)
    
    # 安装依赖
    print("安装 Windows 依赖...")
    wine_python = os.path.expanduser('~/.wine/drive_c/Python311/python.exe')
    result = run_cmd(['wine', wine_python, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=wine_dir)
    if result != 0:
        print("依赖安装失败")
        return False
    
    # 运行 PyInstaller
    print("运行 Windows PyInstaller...")
    pyinstaller = os.path.expanduser('~/.wine/drive_c/Python311/Scripts/pyinstaller.exe')
    
    cmd = [
        'wine', pyinstaller,
        '--clean',
        '--name', APP_NAME,
        '--onefile',
        '--console',
        '--noupx',
    ]
    
    # 添加文件
    for file in INCLUDE_FILES:
        cmd.extend(['--add-data', f'{file};{file}'])
    
    # 添加隐藏导入
    for imp in HIDDEN_IMPORTS:
        cmd.extend(['--hidden-import', imp])
    
    # 排除模块
    for mod in EXCLUDE_MODULES:
        cmd.extend(['--exclude-module', mod])
    
    # 添加入口文件
    cmd.append('app.py')
    
    result = run_cmd(cmd, cwd=wine_dir)
    if result != 0:
        print(f"Windows 打包失败，返回码: {result}")
        return False
    
    # 复制结果到 release 目录
    os.makedirs(RELEASE_DIR, exist_ok=True)
    
    # 查找可执行文件
    exe_path = os.path.join(wine_dir, 'dist', f'{APP_NAME}.exe')
    if not os.path.exists(exe_path):
        print(f"找不到可执行文件: {exe_path}")
        return False
    
    # 创建版本目录
    version_dir = f"{APP_NAME}_v{VERSION}_windows_x64"
    version_path = os.path.join(RELEASE_DIR, version_dir)
    os.makedirs(version_path, exist_ok=True)
    
    # 复制可执行文件
    shutil.copy(exe_path, version_path)
    
    # 创建 README
    create_readme(version_path, "Windows")
    
    # 创建压缩包
    create_zip(version_path, version_dir)
    
    print(f"Windows 版本打包完成: {version_dir}")
    return True

def create_readme(path, platform):
    """创建 README 文件"""
    readme_content = f"""# {APP_NAME} v{VERSION}

## 运行环境
- {platform}

## 使用方法

### 启动应用
```bash
# {platform} 版本
./{APP_NAME}{'.exe' if platform == 'Windows' else ''}
```

### 访问地址
浏览器打开: http://localhost:5000

## 功能
- 小红书助手
- 养号功能
- PDF 转换
- 文件传输
"""
    
    readme_path = os.path.join(path, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

def create_zip(path, name):
    """创建 ZIP 压缩包"""
    import zipfile
    
    zip_name = f"{name}.zip"
    zip_path = os.path.join(RELEASE_DIR, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, RELEASE_DIR)
                zipf.write(file_path, arcname)

def main():
    print("="*60)
    print(f"{APP_NAME} 交叉编译工具 v{VERSION}")
    print("="*60)
    print()
    
    # 检查平台
    if platform.system() != 'Darwin':
        print("错误: 此脚本仅支持在 macOS 上运行")
        return 1
    
    # 清理旧文件
    print("清理旧文件...")
    for dir_name in [RELEASE_DIR, 'build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 打包 macOS 版本
    if not build_macos():
        return 1
    
    # 打包 Windows 版本
    if not build_windows():
        print("Windows 版本打包失败，但 macOS 版本已成功")
        return 0
    
    print("\n" + "="*60)
    print("所有版本打包完成！")
    print("="*60)
    print()
    print(f"输出目录: {RELEASE_DIR}")
    print(f"版本: {VERSION}")
    print()
    
    # 打开输出目录
    subprocess.run(['open', RELEASE_DIR])
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
