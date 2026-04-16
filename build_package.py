import os
import sys
import zipfile

release_dir = 'release'
os.makedirs(release_dir, exist_ok=True)

if sys.platform == 'win32':
    version_dir = 'xhs_helper_v1.0.0_windows_x64'
    exe_path = os.path.join('dist', 'xhs_helper.exe')
else:
    if sys.platform == 'darwin':
        arch = os.uname().machine
    else:
        arch = 'x64'
    version_dir = f'xhs_helper_v1.0.0_{sys.platform}_{arch}'
    exe_path = os.path.join('dist', 'xhs_helper')

version_path = os.path.join(release_dir, version_dir)
os.makedirs(version_path, exist_ok=True)

# 复制可执行文件
if os.path.exists(exe_path):
    import shutil
    shutil.copy(exe_path, version_path)
else:
    print(f"Error: Executable not found: {exe_path}")
    sys.exit(1)

# 创建 README
readme_content = f'# xhs_helper v1.0.0\n\n'
if sys.platform == 'win32':
    readme_content += '## Windows 版本\n\n'
    readme_content += '## 使用方法: 双击 xhs_helper.exe\n\n'
else:
    readme_content += f'## {sys.platform} 版本\n\n'
    readme_content += '## 使用方法: chmod +x xhs_helper && ./xhs_helper\n\n'

readme_path = os.path.join(version_path, 'README.md')
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)

# 创建 ZIP 压缩包
zip_name = f'{version_dir}.zip'
zip_path = os.path.join(release_dir, zip_name)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(version_path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, release_dir)
            zipf.write(file_path, arcname)

print(f'Created release package: {zip_path}')
