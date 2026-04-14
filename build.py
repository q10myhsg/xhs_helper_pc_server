#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
RELEASE_DIR = BASE_DIR / 'release'
OBFUSCATED_DIR = BASE_DIR / '.obfuscated'

def print_step(message):
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or BASE_DIR,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def clean_build_dirs():
    """清理构建目录"""
    print_step("清理构建目录")
    
    dirs_to_clean = [
        RELEASE_DIR,
        OBFUSCATED_DIR,
        BASE_DIR / 'build',
        BASE_DIR / 'dist',
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"删除: {dir_path}")
            shutil.rmtree(dir_path)
    
    print("清理完成")

def check_dependencies():
    """检查并安装依赖"""
    print_step("检查构建依赖")
    
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        if not run_command('pip install -r build_requirements.txt'):
            print("错误: 安装依赖失败")
            return False
    
    try:
        import pyarmor
        print("✓ pyarmor 已安装")
    except ImportError:
        print("警告: pyarmor 未安装，将跳过混淆步骤")
    
    return True

def obfuscate_code():
    """使用 pyarmor 混淆代码"""
    print_step("混淆 Python 代码")
    
    try:
        import pyarmor
    except ImportError:
        print("跳过混淆步骤（pyarmor 未安装）")
        return False
    
    # 创建混淆目录
    OBFUSCATED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 需要混淆的文件和目录
    files_to_obfuscate = [
        'app.py',
        'license_manager.py',
        'machine_code.py',
        'pdf_converter.py',
        'file_transfer.py',
        'config_manager.py',
        'db_manager.py',
        'utils.py',
        'clear_usage.py',
        'migrate_keywords.py',
        'test_activation_code.py',
        'test_modules.py',
        'test_pc_server_activation.py',
    ]
    
    dirs_to_obfuscate = [
        'xhs_nurturing',
        'create_notes',
    ]
    
    # 复制静态资源（不混淆）
    static_dirs = ['templates', 'static', 'config', 'resources']
    for dir_name in static_dirs:
        src = BASE_DIR / dir_name
        dst = OBFUSCATED_DIR / dir_name
        if src.exists():
            print(f"复制静态资源: {dir_name}")
            shutil.copytree(src, dst)
    
    # 混淆单个文件
    for file_name in files_to_obfuscate:
        src = BASE_DIR / file_name
        if src.exists():
            print(f"混淆: {file_name}")
            cmd = f'pyarmor gen -O "{OBFUSCATED_DIR}" "{src}"'
            if not run_command(cmd):
                print(f"警告: 混淆 {file_name} 失败，直接复制")
                shutil.copy2(src, OBFUSCATED_DIR / file_name)
    
    # 混淆目录
    for dir_name in dirs_to_obfuscate:
        src = BASE_DIR / dir_name
        if src.exists():
            print(f"混淆目录: {dir_name}")
            cmd = f'pyarmor gen -O "{OBFUSCATED_DIR}" -r "{src}"'
            if not run_command(cmd):
                print(f"警告: 混淆 {dir_name} 失败，直接复制")
                shutil.copytree(src, OBFUSCATED_DIR / dir_name)
    
    print("代码混淆完成")
    return True

def build_with_pyinstaller(source_dir):
    """使用 PyInstaller 打包"""
    print_step("使用 PyInstaller 打包")
    
    # 复制 spec 文件到源码目录
    spec_file = BASE_DIR / 'xhs_helper.spec'
    if spec_file.exists():
        shutil.copy2(spec_file, source_dir / 'xhs_helper.spec')
    
    # 运行 PyInstaller
    cmd = f'pyinstaller --clean "{source_dir / "xhs_helper.spec"}"'
    if not run_command(cmd, cwd=source_dir):
        print("错误: PyInstaller 打包失败")
        return False
    
    return True

def prepare_release():
    """准备发布文件"""
    print_step("准备发布文件")
    
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    
    dist_dir = BASE_DIR / 'dist'
    if not dist_dir.exists():
        # 检查混淆目录下的 dist
        dist_dir = OBFUSCATED_DIR / 'dist'
    
    if not dist_dir.exists():
        print("错误: 找不到 dist 目录")
        return False
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == 'darwin':
        # macOS
        app_path = dist_dir / 'xhs_helper.app'
        if app_path.exists():
            version = '1.0.0'
            zip_name = f'xhs_helper_mac_{arch}_v{version}.zip'
            zip_path = RELEASE_DIR / zip_name
            
            print(f"创建 macOS 压缩包: {zip_name}")
            
            # 使用 zip 命令打包
            cmd = f'cd "{dist_dir}" && zip -r "{zip_path}" "xhs_helper.app"'
            if run_command(cmd):
                print(f"✓ 已生成: {zip_path}")
                return True
    elif system == 'windows':
        # Windows
        exe_path = dist_dir / 'xhs_helper.exe'
        if exe_path.exists():
            version = '1.0.0'
            zip_name = f'xhs_helper_windows_{arch}_v{version}.zip'
            zip_path = RELEASE_DIR / zip_name
            
            print(f"创建 Windows 压缩包: {zip_name}")
            
            # 复制整个目录内容
            temp_dir = dist_dir / 'xhs_helper'
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
            for item in dist_dir.iterdir():
                if item.name != 'xhs_helper':
                    if item.is_dir():
                        shutil.copytree(item, temp_dir / item.name)
                    else:
                        shutil.copy2(item, temp_dir / item.name)
            
            # 使用 zip 打包
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir.parent)
                        zipf.write(file_path, arcname)
            
            shutil.rmtree(temp_dir)
            print(f"✓ 已生成: {zip_path}")
            return True
    
    print("警告: 未能找到可执行文件进行打包")
    return False

def main():
    print("小红书助手 - 打包工具")
    print(f"平台: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # 1. 清理
    clean_build_dirs()
    
    # 2. 检查依赖
    if not check_dependencies():
        return 1
    
    # 3. 尝试混淆（如果有 pyarmor）
    source_dir = BASE_DIR
    if obfuscate_code():
        source_dir = OBFUSCATED_DIR
    
    # 4. 打包
    if not build_with_pyinstaller(source_dir):
        return 1
    
    # 5. 准备发布
    if prepare_release():
        print_step("构建完成!")
        print(f"发布文件位于: {RELEASE_DIR}")
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
