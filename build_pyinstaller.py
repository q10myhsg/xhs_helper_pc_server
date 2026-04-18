import os
import subprocess
import sys
import uiautomator2

# 根据平台选择分隔符
if sys.platform == 'win32':
    sep = ';'
else:
    sep = ':'

# 获取 uiautomator2 的 assets 目录路径
uiautomator2_path = os.path.dirname(uiautomator2.__file__)
uiautomator2_assets_path = os.path.join(uiautomator2_path, 'assets')

# 构建 PyInstaller 命令
cmd = [
    'pyinstaller',
    '--clean',
    '--name', 'xhs_helper',
    '--onefile',
    '--windowed',  # 使用窗口模式，不显示控制台
    '--noupx',
    '--add-data', f'templates{sep}templates',
    '--add-data', f'static{sep}static',
    '--add-data', f'config{sep}config',
    '--add-data', f'resources{sep}resources',
    '--add-data', f'create_notes{sep}create_notes',
    '--add-data', f'xhs_nurturing{sep}xhs_nurturing',
    '--add-data', f'{uiautomator2_assets_path}{sep}uiautomator2/assets',
    '--hidden-import', 'flask',
    '--hidden-import', 'werkzeug',
    '--hidden-import', 'uiautomator2',
    '--hidden-import', 'PIL',
    '--hidden-import', 'bs4',
    '--hidden-import', 'lxml',
    '--hidden-import', 'pdf2image',
    '--hidden-import', 'PyPDF2',
    '--hidden-import', 'PyMuPDF',
    '--hidden-import', 'fitz',
    '--hidden-import', 'openai',
    '--hidden-import', 'xhs_nurturing',
    '--hidden-import', 'create_notes',
    '--hidden-import', 'license_manager',
    '--hidden-import', 'machine_code',
    '--hidden-import', 'pdf_converter',
    '--hidden-import', 'file_transfer',
    '--hidden-import', 'config_manager',
    '--hidden-import', 'db_manager',
    '--hidden-import', 'utils',
    '--hidden-import', 'env_checker',
    '--hidden-import', 'env_installer',
    '--hidden-import', 'venv_manager',
    '--hidden-import', 'env_setup_gui',
    '--hidden-import', 'tkinter',
    '--hidden-import', 'webview',
    '--hidden-import', 'waitress',
    '--hidden-import', 'uiautomator2_patch',
    'desktop_app.py'
]

print(f"Running PyInstaller with command: {' '.join(cmd)}")
result = subprocess.run(cmd)
sys.exit(result.returncode)
