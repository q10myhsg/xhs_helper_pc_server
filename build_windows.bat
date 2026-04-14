@echo off
chcp 65001 >nul
echo ============================================================
echo   小红书助手 - Windows 打包工具
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] 清理旧的构建文件...
if exist release rmdir /s /q release
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist .obfuscated rmdir /s /q .obfuscated
echo 清理完成
echo.

echo [2/4] 检查并安装依赖...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)
echo 依赖检查完成
echo.

echo [3/4] 开始打包...
python build_simple.py
if errorlevel 1 (
    echo.
    echo 打包失败！
    pause
    exit /b 1
)
echo.

echo [4/4] 打包完成！
echo.
echo 输出文件位于: release\
echo.
dir /b release
echo.
echo ============================================================
pause
