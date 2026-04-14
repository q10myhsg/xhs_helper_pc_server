# 小红书助手 - 打包说明

## 概述

本文档说明如何将小红书助手项目打包成可执行文件，并进行代码混淆保护。

## 前置要求

- Python 3.8 或更高版本
- pip 包管理器

## 快速开始

### 1. 安装构建依赖

```bash
cd xhs_helper_pc_server
pip install -r build_requirements.txt
```

### 2. 运行打包脚本

#### 方式一：完整打包（推荐）

```bash
python build.py
```

这个脚本会：
- 清理旧的构建文件
- 检查并安装依赖
- 使用 pyarmor 混淆代码（如果已安装）
- 使用 PyInstaller 打包
- 生成压缩包到 `release/` 目录

#### 方式二：简易打包

如果 pyarmor 安装有问题，可以使用简化版：

```bash
python build_simple.py
```

这个脚本只使用 PyInstaller 打包，不进行代码混淆。

## 打包产物

构建完成后，在 `release/` 目录下会生成：

### macOS
```
xhs_helper_mac_arm64_v1.0.0.zip  # Apple Silicon
xhs_helper_mac_x86_64_v1.0.0.zip  # Intel
```

### Windows
```
xhs_helper_windows_amd64_v1.0.0.zip
```

## 使用生成的应用

### macOS

1. 解压 zip 文件
2. 将 `xhs_helper.app` 拖到 Applications 文件夹
3. 右键点击 → 打开（首次运行需要允许）
4. 应用会自动打开浏览器访问 http://127.0.0.1:5000

### Windows

1. 解压 zip 文件
2. 运行 `xhs_helper.exe`
3. 允许防火墙访问（如果提示）
4. 应用会自动打开浏览器访问 http://127.0.0.1:5000

## 代码混淆说明

### PyArmor 配置

项目使用 PyArmor 进行代码混淆，主要保护：
- 核心业务逻辑
- 授权验证代码
- 数据库操作

### 混淆选项

默认启用的混淆功能：
- 代码压缩
- 控制流混淆
- 字符串加密
- 名称混淆
- 防调试保护

## 手动打包步骤（高级）

如果需要自定义打包流程，可以按以下步骤操作：

### 1. 安装依赖

```bash
pip install pyinstaller pyarmor
```

### 2. 混淆代码（可选）

```bash
pyarmor gen -O .obfuscated app.py
pyarmor gen -O .obfuscated -r xhs_nurturing/
```

### 3. 复制资源文件

```bash
cp -r templates .obfuscated/
cp -r static .obfuscated/
cp -r config .obfuscated/
cp -r resources .obfuscated/
```

### 4. 使用 PyInstaller 打包

```bash
cd .obfuscated
pyinstaller --clean ../xhs_helper.spec
```

## 常见问题

### Q: 打包后运行提示缺少模块？

A: 在 `xhs_helper.spec` 的 `hiddenimports` 中添加缺失的模块。

### Q: macOS 上提示"无法打开，因为无法验证开发者"？

A: 右键点击应用 → 打开，或者在系统偏好设置 → 安全性与隐私中允许。

### Q: 打包后的文件太大？

A: 可以在 spec 文件中启用 UPX 压缩，或者在 `excludes` 中排除不需要的模块。

### Q: 如何更新版本号？

A: 修改 `xhs_helper.spec` 中的版本信息，以及 `build.py` 中的版本号变量。

## 项目结构

```
xhs_helper_pc_server/
├── app.py                      # 主应用入口
├── start.py                    # 启动脚本（打包后使用）
├── build.py                    # 完整打包脚本
├── build_simple.py             # 简易打包脚本
├── xhs_helper.spec             # PyInstaller 配置
├── build_requirements.txt      # 构建依赖
├── requirements.txt            # 项目依赖
├── templates/                  # HTML 模板
├── static/                     # 静态资源
├── config/                     # 配置文件
├── resources/                  # 资源文件
├── xhs_nurturing/              # 核心模块
├── create_notes/               # 笔记创建模块
└── release/                    # 打包输出目录（构建后生成）
```

## 技术支持

如遇到问题，请检查：
1. Python 版本是否符合要求
2. 所有依赖是否正确安装
3. 防火墙是否允许应用访问网络
4. 是否有足够的磁盘空间进行打包
