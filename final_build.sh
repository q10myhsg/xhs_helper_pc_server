#!/bin/bash

# 最终打包脚本：确保所有依赖都正确处理

# 配置
APP_NAME="xhs_helper"
VERSION="1.0.0"
RELEASE_DIR="release"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo -e "${RED}错误: 找不到 app.py，请在项目根目录运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}${APP_NAME} 最终打包脚本 v${VERSION}${NC}"
echo -e "${GREEN}=============================================${NC}"
echo

# 1. 清理旧文件
echo -e "${YELLOW}[1/5] 清理旧文件...${NC}"
for dir_name in "$RELEASE_DIR" "build" "dist" "__pycache__"; do
    if [ -d "$dir_name" ]; then
        rm -rf "$dir_name"
        echo -e "  ${GREEN}已删除: ${dir_name}${NC}"
    fi
done
for file in "*.spec"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo -e "  ${GREEN}已删除: ${file}${NC}"
    fi
done
echo -e "  ${GREEN}清理完成${NC}"
echo

# 2. 检查依赖
echo -e "${YELLOW}[2/5] 检查依赖...${NC}"
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "  ${YELLOW}正在安装 PyInstaller...${NC}"
    pip3 install pyinstaller
    echo -e "  ${GREEN}安装完成${NC}"
else
    VERSION_PYI=$(python3 -c "import PyInstaller; print(PyInstaller.__version__)" 2>/dev/null)
    echo -e "  ${GREEN}PyInstaller ${VERSION_PYI}${NC}"
fi

# 安装项目依赖
echo -e "  ${YELLOW}安装项目依赖...${NC}"
pip3 install -r requirements.txt
echo -e "  ${GREEN}依赖安装完成${NC}"
echo

# 3. 运行 PyInstaller
echo -e "${YELLOW}[3/5] 开始打包...${NC}"

# 构建命令
CMD="python3 -m PyInstaller --clean --name $APP_NAME --onefile --console --noupx \
    --add-data 'templates:templates' \
    --add-data 'static:static' \
    --add-data 'config:config' \
    --add-data 'resources:resources' \
    --add-data 'create_notes:create_notes' \
    --add-data 'xhs_nurturing:xhs_nurturing' \
    --hidden-import 'flask' \
    --hidden-import 'werkzeug' \
    --hidden-import 'uiautomator2' \
    --hidden-import 'PIL' \
    --hidden-import 'bs4' \
    --hidden-import 'lxml' \
    --hidden-import 'pdf2image' \
    --hidden-import 'PyPDF2' \
    --hidden-import 'PyMuPDF' \
    --hidden-import 'fitz' \
    --hidden-import 'openai' \
    --hidden-import 'xhs_nurturing' \
    --hidden-import 'create_notes' \
    --hidden-import 'license_manager' \
    --hidden-import 'machine_code' \
    --hidden-import 'pdf_converter' \
    --hidden-import 'file_transfer' \
    --hidden-import 'config_manager' \
    --hidden-import 'db_manager' \
    --hidden-import 'utils' \
    --exclude-module 'matplotlib' \
    --exclude-module 'numpy' \
    --exclude-module 'pandas' \
    --exclude-module 'scipy' \
    --exclude-module 'sklearn' \
    --exclude-module 'skimage' \
    --exclude-module 'scikit-image' \
    --exclude-module 'imageio' \
    --exclude-module 'tkinter' \
    --exclude-module 'IPython' \
    --exclude-module 'jupyter' \
    --exclude-module 'notebook' \
    --exclude-module 'PyQt5' \
    --exclude-module 'PyQt6' \
    --exclude-module 'PySide2' \
    --exclude-module 'PySide6' \
    --exclude-module 'traitlets' \
    --exclude-module 'pytest' \
    --exclude-module 'unittest' \
    app.py"

echo -e "  ${YELLOW}执行命令...${NC}"
echo
eval $CMD

if [ $? -ne 0 ]; then
    echo -e "${RED}  打包失败${NC}"
    exit 1
fi

echo
echo -e "  ${GREEN}打包完成${NC}"
echo

# 4. 创建发布包
echo -e "${YELLOW}[4/5] 创建发布包...${NC}"
mkdir -p "$RELEASE_DIR"

# 检查输出目录
if [ ! -d "dist" ]; then
    echo -e "${RED}  错误: 找不到输出目录: dist${NC}"
    exit 1
fi

# 查找可执行文件
EXE_NAME="$APP_NAME"
EXE_PATH="dist/$EXE_NAME"

if [ ! -f "$EXE_PATH" ]; then
    echo -e "${RED}  错误: 找不到可执行文件: $EXE_PATH${NC}"
    exit 1
fi

# 创建版本目录
VERSION_DIR="${APP_NAME}_v${VERSION}_macos_$(uname -m)"
VERSION_PATH="$RELEASE_DIR/$VERSION_DIR"
mkdir -p "$VERSION_PATH"

# 复制可执行文件
cp "$EXE_PATH" "$VERSION_PATH"
echo -e "  ${GREEN}复制可执行文件: $EXE_NAME${NC}"

# 创建 README
README_CONTENT="# $APP_NAME v$VERSION

## 运行环境
- macOS $(uname -m)

## 使用方法

### 启动应用
```bash
chmod +x $EXE_NAME
./$EXE_NAME
```

### 访问地址
浏览器打开: http://localhost:5000

## 功能
- 小红书助手
- 养号功能
- PDF 转换
- 文件传输

## 依赖说明
- Flask 2.3.2
- uiautomator2 3.2.10
- Pillow 10.4.0
- requests 2.27.1
- beautifulsoup4 4.12.2
- lxml 5.1.0
- pdf2image 1.16.3
- PyPDF2 3.0.1
- PyMuPDF 1.23.22
- openai 1.3.0"

echo "$README_CONTENT" > "$VERSION_PATH/README.md"
echo -e "  ${GREEN}创建 README.md${NC}"

# 创建压缩包
ZIP_NAME="$VERSION_DIR.zip"
ZIP_PATH="$RELEASE_DIR/$ZIP_NAME"

cd "$RELEASE_DIR"
zip -r "$ZIP_NAME" "$VERSION_DIR"
cd ..

echo -e "  ${GREEN}创建压缩包: $ZIP_NAME${NC}"

# 5. 测试可执行文件
echo -e "${YELLOW}[5/5] 测试可执行文件...${NC}"

# 授予执行权限
chmod +x "$EXE_PATH"

# 尝试运行 5 秒
echo -e "  ${YELLOW}尝试启动应用...${NC}"
"$EXE_PATH" &
PID=$!
sleep 5
kill $PID

echo -e "  ${GREEN}测试完成${NC}"

# 显示结果
echo
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  打包完成！${NC}"
echo -e "${GREEN}=============================================${NC}"
echo
echo -e "${GREEN}输出目录: $RELEASE_DIR${NC}"
echo -e "${GREEN}版本: $VERSION${NC}"
echo -e "${GREEN}平台: macOS $(uname -m)${NC}"
echo
echo -e "${YELLOW}文件列表:${NC}"
echo -e "  - ${VERSION_DIR}/"
echo -e "    - ${EXE_NAME}"
echo -e "    - README.md"
echo -e "  - ${ZIP_NAME}"
echo

# 检查文件大小
FILE_SIZE=$(du -h "$VERSION_PATH/$EXE_NAME" | cut -f1)
echo -e "${GREEN}可执行文件大小: $FILE_SIZE${NC}"
echo

echo -e "${GREEN}使用方法:${NC}"
echo -e "  解压 $ZIP_NAME"
echo -e "  运行 chmod +x $EXE_NAME"
echo -e "  运行 ./$EXE_NAME"
echo -e "  浏览器访问 http://localhost:5000"

# 打开输出目录
echo -e "${YELLOW}打开输出目录...${NC}"
open "$RELEASE_DIR"

# 退出
if [ $? -eq 0 ]; then
    exit 0
else
    exit 1
fi
