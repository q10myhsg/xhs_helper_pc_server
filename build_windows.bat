@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 配置
set APP_NAME=xhs_helper
set VERSION=1.0.0
set RELEASE_DIR=release

REM 颜色定义
set RED=9
set GREEN=10
set YELLOW=14
set NC=7

echo.
echo ==============================================
echo %APP_NAME% Windows 打包工具 v%VERSION%
echo ==============================================
echo.

REM 1. 清理旧文件
echo [1/4] 清理旧文件...
for %%d in (%RELEASE_DIR% build dist) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
        echo   已删除: %%d
    )
)
echo   清理完成
echo.

REM 2. 检查 PyInstaller
echo [2/4] 检查 PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo   正在安装 PyInstaller...
    pip install pyinstaller
    echo   安装完成
) else (
    for /f %%i in ('python -c "import PyInstaller; print(PyInstaller.__version__)" 2^>nul') do set VERSION_PYI=%%i
    echo   PyInstaller !VERSION_PYI!
)
echo.

REM 3. 运行 PyInstaller
echo [3/4] 开始打包...

REM 构建命令
set CMD=python -m PyInstaller --clean --name %APP_NAME% --onefile --console --noupx ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "config;config" ^
    --add-data "resources;resources" ^
    --add-data "create_notes;create_notes" ^
    --add-data "xhs_nurturing;xhs_nurturing" ^
    --hidden-import "flask" ^
    --hidden-import "werkzeug" ^
    --hidden-import "uiautomator2" ^
    --hidden-import "PIL" ^
    --hidden-import "bs4" ^
    --hidden-import "lxml" ^
    --hidden-import "xhs_nurturing" ^
    --hidden-import "create_notes" ^
    --hidden-import "license_manager" ^
    --hidden-import "machine_code" ^
    --hidden-import "pdf_converter" ^
    --hidden-import "file_transfer" ^
    --hidden-import "config_manager" ^
    --hidden-import "db_manager" ^
    --hidden-import "utils" ^
    --exclude-module "matplotlib" ^
    --exclude-module "numpy" ^
    --exclude-module "pandas" ^
    --exclude-module "scipy" ^
    --exclude-module "sklearn" ^
    --exclude-module "skimage" ^
    --exclude-module "scikit-image" ^
    --exclude-module "imageio" ^
    --exclude-module "tkinter" ^
    --exclude-module "IPython" ^
    --exclude-module "jupyter" ^
    --exclude-module "notebook" ^
    --exclude-module "PyQt5" ^
    --exclude-module "PyQt6" ^
    --exclude-module "PySide2" ^
    --exclude-module "PySide6" ^
    --exclude-module "traitlets" ^
    --exclude-module "pytest" ^
    --exclude-module "unittest" ^
    app.py

echo   执行命令...
echo.
!CMD!

if errorlevel 1 (
    echo.
    echo   打包失败
    pause
    exit /b 1
)

echo.
echo   打包完成
echo.

REM 4. 创建发布包
echo [4/4] 创建发布包...
mkdir "%RELEASE_DIR%" 2>nul

REM 检查输出目录
if not exist "dist" (
    echo   错误: 找不到输出目录: dist
    pause
    exit /b 1
)

REM 查找可执行文件
set EXE_NAME=%APP_NAME%.exe
set EXE_PATH=dist\%EXE_NAME%

if not exist "%EXE_PATH%" (
    echo   错误: 找不到可执行文件: %EXE_PATH%
    pause
    exit /b 1
)

REM 创建版本目录
set ARCH=x64
if "%PROCESSOR_ARCHITECTURE%" equ "x86" set ARCH=x86
set VERSION_DIR=%APP_NAME%_v%VERSION%_windows_%ARCH%
set VERSION_PATH=%RELEASE_DIR%\%VERSION_DIR%
mkdir "%VERSION_PATH%" 2>nul

REM 复制可执行文件
copy "%EXE_PATH%" "%VERSION_PATH%"
echo   复制可执行文件: %EXE_NAME%

REM 创建 README
set README_CONTENT=# %APP_NAME% v%VERSION%

## 运行环境
- Windows %ARCH%

## 使用方法

### 启动应用
```bash
%EXE_NAME%
```

### 访问地址
浏览器打开: http://localhost:5000

## 功能
- 小红书助手
- 养号功能
- PDF 转换
- 文件传输

echo !README_CONTENT! > "%VERSION_PATH%\README.md"
echo   创建 README.md

REM 创建压缩包
set ZIP_NAME=%VERSION_DIR%.zip
set ZIP_PATH=%RELEASE_DIR%\%ZIP_NAME%

powershell -Command "Compress-Archive -Path '%VERSION_PATH%\*' -DestinationPath '%ZIP_PATH%' -Force"
echo   创建压缩包: %ZIP_NAME%

REM 显示结果
echo.
echo ==============================================
echo   打包完成！
echo ==============================================
echo.
echo 输出目录: %RELEASE_DIR%
echo 版本: %VERSION%
echo 平台: Windows %ARCH%
echo.
echo 文件列表:
echo   - %VERSION_DIR%\
echo     - %EXE_NAME%
echo     - README.md
echo   - %ZIP_NAME%
echo.
echo 使用方法:
echo   解压 %ZIP_NAME%
echo   运行 %EXE_NAME%
echo   浏览器访问 http://localhost:5000
echo.

REM 打开输出目录
echo 打开输出目录...
start "" "%RELEASE_DIR%"

pause
