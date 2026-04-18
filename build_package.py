import os
import sys
import zipfile

release_dir = 'release'
os.makedirs(release_dir, exist_ok=True)

if sys.platform == 'win32':
    version_dir = 'xhs_helper_v1.0.0_windows_x64'
    exe_path = os.path.join('dist', 'xhs_helper.exe')
    exe_name = 'xhs_helper.exe'
else:
    if sys.platform == 'darwin':
        arch = os.uname().machine
    else:
        arch = 'x64'
    version_dir = f'xhs_helper_v1.0.0_{sys.platform}_{arch}'
    exe_path = os.path.join('dist', 'xhs_helper')
    exe_name = 'xhs_helper'

# 创建 README 内容
readme_content = f'# xhs_helper v1.0.0\n\n'
if sys.platform == 'win32':
    readme_content += '## Windows 版本\n\n'
    readme_content += '## 使用方法: 双击 xhs_helper.exe\n\n'
else:
    readme_content += f'## {sys.platform} 版本\n\n'
    readme_content += '## 使用方法: chmod +x xhs_helper && ./xhs_helper\n\n'

# 创建 ZIP 压缩包 - 直接写入，不创建中间文件夹
zip_name = f'{version_dir}.zip'
zip_path = os.path.join(release_dir, zip_name)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # 添加可执行文件
    if os.path.exists(exe_path):
        arcname = os.path.join(version_dir, exe_name)
        zipf.write(exe_path, arcname)
    else:
        print(f"Error: Executable not found: {exe_path}")
        sys.exit(1)
    
    # 添加 README
    from io import BytesIO
    readme_bytes = readme_content.encode('utf-8')
    readme_arcname = os.path.join(version_dir, 'README.md')
    zipf.writestr(readme_arcname, readme_bytes)

print(f'Created release package: {zip_path}')
