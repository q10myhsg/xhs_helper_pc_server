#!/usr/bin/env python3
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

def main():
    print("="*60)
    print(f"{APP_NAME} 打包工具 v{VERSION}")
    print("="*60)
    print()
    
    # 检查平台
    system = platform.system()
    arch = platform.machine()
    print(f"平台: {system} {arch}")
    print()
    
    # 1. 清理旧文件
    print("[1/4] 清理旧文件...")
    for dir_name in [RELEASE_DIR, 'build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  已删除: {dir_name}")
    print("  清理完成")
    print()
    
    # 2. 检查 PyInstaller
    print("[2/4] 检查 PyInstaller...")
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  正在安装 PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("  ✓ 安装完成")
    print()
    
    # 3. 运行 PyInstaller
    print("[3/4] 开始打包...")
    
    # 构建命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--name', APP_NAME,
        '--onefile',
        '--console',
        '--noupx',
    ]
    
    # 添加文件
    sep = ';' if system == 'Windows' else ':'
    for file in INCLUDE_FILES:
        cmd.extend(['--add-data', f'{file}{sep}{file}'])
    
    # 添加隐藏导入
    for imp in HIDDEN_IMPORTS:
        cmd.extend(['--hidden-import', imp])
    
    # 排除模块
    for mod in EXCLUDE_MODULES:
        cmd.extend(['--exclude-module', mod])
    
    # 添加入口文件
    cmd.append('app.py')
    
    print(f"  执行命令: {' '.join(cmd[:10])}...")
    print()
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  ✗ 打包失败，返回码: {result.returncode}")
        return 1
    
    print()
    print("  ✓ 打包完成")
    print()
    
    # 4. 创建发布包
    print("[4/4] 创建发布包...")
    os.makedirs(RELEASE_DIR, exist_ok=True)
    
    # 复制可执行文件
    dist_dir = 'dist'
    if not os.path.exists(dist_dir):
        print(f"  ✗ 错误: 找不到输出目录: {dist_dir}")
        return 1
    
    # 查找可执行文件
    exe_name = APP_NAME
    if system == 'Windows':
        exe_name += '.exe'
    
    exe_path = os.path.join(dist_dir, exe_name)
    if not os.path.exists(exe_path):
        print(f"  ✗ 错误: 找不到可执行文件: {exe_path}")
        return 1
    
    # 创建版本目录
    version_dir = f"{APP_NAME}_v{VERSION}_{system.lower()}_{arch.lower()}"
    version_path = os.path.join(RELEASE_DIR, version_dir)
    os.makedirs(version_path, exist_ok=True)
    
    # 复制可执行文件
    shutil.copy(exe_path, version_path)
    print(f"  复制可执行文件: {exe_name}")
    
    # 创建 README
    readme_content = f"""# {APP_NAME} v{VERSION}

## 运行环境
- {system} {arch}

## 使用方法

### 启动应用
```bash
./{exe_name}
```

### 访问地址
浏览器打开: http://localhost:5000

## 功能
- 小红书助手
- 养号功能
- PDF 转换
- 文件传输
"""
    
    readme_path = os.path.join(version_path, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  创建 README.md")
    
    # 创建压缩包
    zip_name = f"{version_dir}.zip"
    zip_path = os.path.join(RELEASE_DIR, zip_name)
    
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(version_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, RELEASE_DIR)
                zipf.write(file_path, arcname)
    
    print(f"  创建压缩包: {zip_name}")
    
    # 显示结果
    print()
    print("="*60)
    print("  打包完成！")
    print("="*60)
    print()
    print(f"输出目录: {RELEASE_DIR}")
    print(f"版本: {VERSION}")
    print(f"平台: {system} {arch}")
    print()
    print("文件列表:")
    print(f"  - {version_dir}/")
    print(f"    - {exe_name}")
    print(f"    - README.md")
    print(f"  - {zip_name}")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
