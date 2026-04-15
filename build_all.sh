#!/bin/bash

# 快速打包脚本：在 macOS 上同时打包 macOS 和 Windows 版本
# 注意：Windows 版本需要先安装 Wine 和 Windows Python

# 配置
APP_NAME="xhs_helper"
VERSION="1.0.0"
RELEASE_DIR="release"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在 macOS 上
if [ "$(uname -s)" != "Darwin" ]; then
    echo -e "${RED}错误: 此脚本仅支持在 macOS 上运行${NC}"
    exit 1
fi

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}${APP_NAME} 一键打包工具 v${VERSION}${NC}"
echo -e "${GREEN}=============================================${NC}"
echo

# 清理旧文件
echo -e "${YELLOW}清理旧文件...${NC}"
for dir_name in "$RELEASE_DIR" "build" "dist"; do
    if [ -d "$dir_name" ]; then
        rm -rf "$dir_name"
        echo -e "  ${GREEN}已删除: ${dir_name}${NC}"
    fi
done
mkdir -p "$RELEASE_DIR"
echo

# 1. 打包 macOS 版本
echo -e "${YELLOW}[1/2] 打包 macOS 版本...${NC}"

python3 -m PyInstaller --clean --name "$APP_NAME" --onefile --console --noupx \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "config:config" \
    --add-data "resources:resources" \
    --add-data "create_notes:create_notes" \
    --add-data "xhs_nurturing:xhs_nurturing" \
    --hidden-import "flask" \
    --hidden-import "werkzeug" \
    --hidden-import "uiautomator2" \
    --hidden-import "PIL" \
    --hidden-import "bs4" \
    --hidden-import "lxml" \
    --hidden-import "xhs_nurturing" \
    --hidden-import "create_notes" \
    --hidden-import "license_manager" \
    --hidden-import "machine_code" \
    --hidden-import "pdf_converter" \
    --hidden-import "file_transfer" \
    --hidden-import "config_manager" \
    --hidden-import "db_manager" \
    --hidden-import "utils" \
    app.py

if [ $? -eq 0 ]; then
    # 创建 macOS 发布包
    MAC_DIR="${RELEASE_DIR}/${APP_NAME}_v${VERSION}_macos_$(uname -m)"
    mkdir -p "$MAC_DIR"
    cp "dist/$APP_NAME" "$MAC_DIR"
    
    # 创建 README
    echo "# $APP_NAME v$VERSION" > "$MAC_DIR/README.md"
    echo "## macOS 版本" >> "$MAC_DIR/README.md"
    echo "## 使用方法:" >> "$MAC_DIR/README.md"
    echo "```bash" >> "$MAC_DIR/README.md"
    echo "chmod +x $APP_NAME" >> "$MAC_DIR/README.md"
    echo "./$APP_NAME" >> "$MAC_DIR/README.md"
    echo "```" >> "$MAC_DIR/README.md"
    echo "## 访问地址: http://localhost:5000" >> "$MAC_DIR/README.md"
    
    # 压缩
    zip -r "${MAC_DIR}.zip" "$MAC_DIR"
    
    echo -e "  ${GREEN}macOS 版本打包完成${NC}"
else
    echo -e "${RED}  macOS 版本打包失败${NC}"
fi

echo

# 2. 尝试打包 Windows 版本
echo -e "${YELLOW}[2/2] 尝试打包 Windows 版本...${NC}"

# 检查 Wine 是否安装
if ! command -v wine &> /dev/null; then
    echo -e "${YELLOW}  Wine 未安装，跳过 Windows 版本打包${NC}"
    echo -e "  ${YELLOW}  如需打包 Windows 版本，请安装 Wine: brew install --cask wine-stable${NC}"
else
    echo -e "  ${YELLOW}  Wine 已安装，开始打包 Windows 版本${NC}"
    echo -e "  ${YELLOW}  注意: 需要先安装 Windows 版本的 Python 和 PyInstaller${NC}"
    
    # 这里可以添加 Windows 版本打包逻辑
    # 由于需要配置 Wine 环境，建议使用 GitHub Actions 方式
fi

echo
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}打包完成！${NC}"
echo -e "${GREEN}=============================================${NC}"
echo
echo -e "${GREEN}输出目录: $RELEASE_DIR${NC}"
echo
echo -e "${YELLOW}文件列表:${NC}"
ls -la "$RELEASE_DIR"
echo

# 打开输出目录
open "$RELEASE_DIR"

# 退出
if [ $? -eq 0 ]; then
    exit 0
else
    exit 1
fi
