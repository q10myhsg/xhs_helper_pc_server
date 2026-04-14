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
    # 清理 spec 文件缓存
    for spec_file in BASE_DIR.glob('*.spec'):
        if spec_file.name not in ['xhs_helper_simple.spec']:
            spec_file.unlink()
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
    
    # 使用简化的 spec 文件
    spec_file = BASE_DIR / 'xhs_helper_simple.spec'
    
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_file)]
    
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
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    version = '1.0.0'
    
    zip_name = f'xhs_helper_{system}_{arch}_v{version}.zip'
    zip_path = RELEASE_DIR / zip_name
    
    print(f"  创建: {zip_name}")
    
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in dist_dir.iterdir():
            if item.is_dir():
                for root, dirs, files in os.walk(item):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(dist_dir)
                        zipf.write(file_path, arcname)
            else:
                arcname = item.relative_to(dist_dir)
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
    print(f"  2. 运行 xhs_helper/xhs_helper")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
