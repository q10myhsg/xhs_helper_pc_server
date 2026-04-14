#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
RELEASE_DIR = BASE_DIR / 'release'

def main():
    print("="*60)
    print("  小红书助手 - 打包工具")
    print("="*60)
    print()
    
    print(f"平台: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    print()
    
    # 1. 清理
    print("[1/4] 清理旧文件...")
    for dir_name in ['release', 'build', 'dist']:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
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
        '--name', 'xhs_helper',
        '--onefile',
        '--console',
        '--add-data', 'templates:templates',
        '--add-data', 'static:static',
        '--add-data', 'config:config',
        '--add-data', 'resources:resources',
        '--add-data', 'create_notes:create_notes',
        '--add-data', 'xhs_nurturing:xhs_nurturing',
        '--hidden-import', 'flask',
        '--hidden-import', 'werkzeug',
        '--hidden-import', 'uiautomator2',
        '--hidden-import', 'PIL',
        '--hidden-import', 'bs4',
        '--hidden-import', 'lxml',
        '--hidden-import', 'xhs_nurturing',
        '--hidden-import', 'create_notes',
        '--hidden-import', 'license_manager',
        '--hidden-import', 'machine_code',
        '--hidden-import', 'pdf_converter',
        '--hidden-import', 'file_transfer',
        '--hidden-import', 'config_manager',
        '--hidden-import', 'db_manager',
        '--hidden-import', 'utils',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'numpy',
        '--exclude-module', 'pandas',
        '--exclude-module', 'scipy',
        '--exclude-module', 'sklearn',
        '--exclude-module', 'skimage',
        '--exclude-module', 'scikit-image',
        '--exclude-module', 'imageio',
        '--exclude-module', 'tkinter',
        '--exclude-module', 'IPython',
        '--exclude-module', 'jupyter',
        '--exclude-module', 'notebook',
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PyQt6',
        '--exclude-module', 'PySide2',
        '--exclude-module', 'PySide6',
        '--exclude-module', 'traitlets',
        '--exclude-module', 'pytest',
        '--exclude-module', 'unittest',
        'app.py'
    ]
    
    # Windows 使用分号作为分隔符
    if platform.system() == 'Windows':
        for i in range(len(cmd)):
            if cmd[i].startswith('--add-data'):
                cmd[i] = cmd[i].replace(':', ';')
    
    print(f"  执行 PyInstaller...")
    print()
    
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"  ✗ 打包失败，返回码: {result.returncode}")
        return 1
    
    print()
    print("  ✓ 打包完成")
    print()
    
    # 4. 创建压缩包
    print("[4/4] 创建发布包...")
    RELEASE_DIR.mkdir(exist_ok=True)
    
    dist_dir = BASE_DIR / 'dist'
    if not dist_dir.exists():
        print(f"  ✗ 错误: 找不到输出目录: {dist_dir}")
        return 1
    
    # 查找输出文件
    exe_path = None
    if (dist_dir / 'xhs_helper').exists():
        exe_path = dist_dir / 'xhs_helper'
    elif (dist_dir / 'xhs_helper.exe').exists():
        exe_path = dist_dir / 'xhs_helper.exe'
    
    if not exe_path:
        print(f"  ✗ 错误: 找不到可执行文件")
        return 1
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    version = '1.0.0'
    
    zip_name = f'xhs_helper_{system}_{arch}_v{version}.zip'
    zip_path = RELEASE_DIR / zip_name
    
    print(f"  创建: {zip_name}")
    
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(exe_path, arcname=exe_path.name)
    
    file_size = zip_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ 已生成: {zip_path}")
    print(f"  文件大小: {file_size:.1f} MB")
    print()
    
    print("="*60)
    print("  打包完成！")
    print("="*60)
    print()
    print(f"输出位置: {RELEASE_DIR}")
    print()
    print("使用方法:")
    print(f"  1. 解压 {zip_name}")
    print(f"  2. 运行 xhs_helper")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
