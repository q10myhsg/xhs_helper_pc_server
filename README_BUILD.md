# 小红书助手 - 打包指南

## 方案一：安装 Xcode Command Line Tools 后打包（推荐）

### 1. 安装 Xcode Command Line Tools
```bash
xcode-select --install
```
安装完成后，等待安装程序完成（可能需要 5-10 分钟）

### 2. 验证安装
```bash
xcode-select -p
```
应该输出类似：`/Library/Developer/CommandLineTools`

### 3. 运行打包脚本
```bash
python3 build_release.py
```

## 方案二：使用虚拟环境直接运行（最简单）

如果您不需要打包成单个可执行文件，可以直接使用 Python 环境运行：

### 1. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python app.py
```

## 方案三：使用 cx_Freeze 打包（备选方案）

如果 PyInstaller 仍然有问题，可以尝试使用 cx_Freeze：

### 1. 安装 cx_Freeze
```bash
pip install cx_Freeze
```

### 2. 创建打包脚本
（已提供 build_cx_freeze.py）

### 3. 运行打包
```bash
python3 build_cx_freeze.py
```

## 已创建的文件说明

- `xhs_final.spec` - PyInstaller 配置文件
- `build_release.py` - PyInstaller 打包脚本
- `build_cx_freeze.py` - cx_Freeze 打包脚本
- `package.py`, `make_dist.py` - 其他尝试的打包脚本
- `test_imports.py` - 模块导入测试脚本

## 代码混淆说明

如果需要代码混淆，可以使用 PyArmor：

### 1. 安装 PyArmor
```bash
pip install pyarmor
```

### 2. 混淆代码
```bash
pyarmor obfuscate --recursive app.py
```

### 3. 打包混淆后的代码
使用 PyInstaller 打包 obfuscated 目录下的代码。
