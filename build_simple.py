#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
RELEASE_DIR = BASE_DIR / 'release'

def print_step(message):
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or BASE_DIR,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def clean_build_dirs():
    print_step("清理构建目录")
    dirs_to_clean = [RELEASE_DIR, BASE_DIR / 'build', BASE_DIR / 'dist']
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"删除: {dir_path}")
            shutil.rmtree(dir_path)
    print("清理完成")

def check_dependencies():
    print_step("检查构建依赖")
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("正在安装 PyInstaller...")
        if run_command('pip install pyinstaller'):
            return True
        print("错误: 安装 PyInstaller 失败")
        return False

def build_with_pyinstaller():
    print_step("使用 PyInstaller 打包")
    
    cmd = (
        'pyinstaller --clean '
        '--name "xhs_helper" '
        '--add-data "templates;templates" '
        '--add-data "static;static" '
        '--add-data "config;config" '
        '--add-data "resources;resources" '
        '--add-data "create_notes;create_notes" '
        '--add-data "xhs_nurturing;xhs_nurturing" '
        '--hidden-import flask '
        '--hidden-import werkzeug '
        '--hidden-import uiautomator2 '
        '--hidden-import PIL '
        '--hidden-import bs4 '
        '--hidden-import lxml '
        '--hidden-import openai '
        '--console '
        'app.py'
    )
    
    # 修正路径分隔符（macOS/Linux 使用 :）
    if platform.system() != 'Windows':
        cmd = cmd.replace(';', ':')
    
    if run_command(cmd):
        print("✓ PyInstaller 打包完成")
        return True
    return False

def prepare_release():
    print_step("准备发布文件")
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    
    dist_dir = BASE_DIR / 'dist'
    if not dist_dir.exists():
        print("错误: 找不到 dist 目录")
        return False
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    version = '1.0.0'
    
    if system == 'darwin':
        app_path = dist_dir / 'xhs_helper.app'
        if app_path.exists():
            zip_name = f'xhs_helper_mac_{arch}_v{version}.zip'
            zip_path = RELEASE_DIR / zip_name
            print(f"创建 macOS 压缩包: {zip_name}")
            cmd = f'cd "{dist_dir}" && zip -r "{zip_path}" "xhs_helper.app"'
            if run_command(cmd):
                print(f"✓ 已生成: {zip_path}")
                return True
    elif system == 'windows':
        exe_dir = dist_dir / 'xhs_helper'
        if exe_dir.exists():
            zip_name = f'xhs_helper_windows_{arch}_v{version}.zip'
            zip_path = RELEASE_DIR / zip_name
            print(f"创建 Windows 压缩包: {zip_name}")
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(exe_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(exe_dir.parent)
                        zipf.write(file_path, arcname)
            print(f"✓ 已生成: {zip_path}")
            return True
    
    print("警告: 未能找到可执行文件进行打包")
    return False

def main():
    print("小红书助手 - 简易打包工具")
    print(f"平台: {platform.system()} {platform.machine()}")
    
    clean_build_dirs()
    
    if not check_dependencies():
        return 1
    
    if not build_with_pyinstaller():
        return 1
    
    if prepare_release():
        print_step("构建完成!")
        print(f"发布文件位于: {RELEASE_DIR}")
        return 0
    
    return 1

if __name__ == '__main__':
    sys.exit(main())
