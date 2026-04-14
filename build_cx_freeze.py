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
    print("  小红书助手 - cx_Freeze 打包工具")
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
    
    # 2. 检查 cx_Freeze
    print("[2/4] 检查 cx_Freeze...")
    try:
        import cx_Freeze
        print(f"  ✓ cx_Freeze {cx_Freeze.__version__}")
    except ImportError:
        print("  正在安装 cx_Freeze...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'cx_Freeze'], check=True)
        import cx_Freeze
        print(f"  ✓ 安装完成: cx_Freeze {cx_Freeze.__version__}")
    print()
    
    # 3. 创建 setup.py
    print("[3/4] 创建配置文件...")
    setup_content = '''
import sys
from cx_Freeze import setup, Executable

# 要包含的文件和目录
include_files = [
    'templates',
    'static',
    'config',
    'resources',
    'create_notes',
    'xhs_nurturing',
]

# 需要排除的模块
excludes = [
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

# 需要包含的模块
packages = [
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

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('app.py', base=base, target_name='xhs_helper')
]

setup(
    name='xhs_helper',
    version='1.0.0',
    description='小红书助手',
    options={
        'build_exe': {
            'include_files': include_files,
            'excludes': excludes,
            'packages': packages,
            'optimize': 0,
        }
    },
    executables=executables
)
'''
    
    setup_file = BASE_DIR / 'setup_cx.py'
    setup_file.write_text(setup_content)
    print("  ✓ 配置文件已创建")
    print()
    
    # 4. 运行 cx_Freeze
    print("[4/4] 开始打包...")
    
    cmd = [sys.executable, 'setup_cx.py', 'build_exe']
    
    print(f"  执行 cx_Freeze...")
    print()
    
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"  ✗ 打包失败，返回码: {result.returncode}")
        return 1
    
    print()
    print("  ✓ 打包完成")
    print()
    
    # 5. 创建压缩包
    print("[5/5] 创建发布包...")
    RELEASE_DIR.mkdir(exist_ok=True)
    
    build_dir = BASE_DIR / 'build'
    if not build_dir.exists():
        print(f"  ✗ 错误: 找不到输出目录: {build_dir}")
        return 1
    
    # 查找输出目录
    exe_dir = None
    for item in build_dir.iterdir():
        if item.is_dir() and item.name.startswith('exe.'):
            exe_dir = item
            break
    
    if not exe_dir:
        print(f"  ✗ 错误: 找不到输出目录")
        return 1
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    version = '1.0.0'
    
    zip_name = f'xhs_helper_{system}_{arch}_v{version}.zip'
    zip_path = RELEASE_DIR / zip_name
    
    print(f"  创建: {zip_name}")
    
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in exe_dir.iterdir():
            if item.is_dir():
                for root, dirs, files in os.walk(item):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(exe_dir)
                        zipf.write(file_path, arcname)
            else:
                arcname = item.relative_to(exe_dir)
                zipf.write(item, arcname)
    
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
