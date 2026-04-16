import os
import subprocess
import sys

# 根据平台选择分隔符
if sys.platform == 'win32':
    sep = ';'
else:
    sep = ':'

# 构建 PyInstaller 命令
cmd = [
    'pyinstaller',
    '--clean',
    '--name', 'xhs_helper',
    '--onefile',
    '--console',
    '--noupx',
    '--add-data', f'templates{sep}templates',
    '--add-data', f'static{sep}static',
    '--add-data', f'config{sep}config',
    '--add-data', f'resources{sep}resources',
    '--add-data', f'create_notes{sep}create_notes',
    '--add-data', f'xhs_nurturing{sep}xhs_nurturing',
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
    'app.py'
]

print(f"Running PyInstaller with command: {' '.join(cmd)}")
result = subprocess.run(cmd)
sys.exit(result.returncode)
