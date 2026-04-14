# 小红书助手 - 打包指南

## 快速开始

### macOS

```bash
cd xhs_helper_pc_server

# 1. 安装构建依赖
pip3 install pyinstaller

# 2. 运行打包脚本
chmod +x build_mac.sh
./build_mac.sh

# 或者直接运行
python3 quick_build.py
```

### Windows

```cmd
cd xhs_helper_pc_server

# 1. 安装构建依赖
pip install pyinstaller

# 2. 运行打包脚本
build_windows.bat
```

## 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `xhs_helper.spec` | PyInstaller 配置文件（已优化） |
| `quick_build.py` | 快速打包脚本（推荐） |
| `build_mac.sh` | macOS 一键打包 |
| `build_windows.bat` | Windows 一键打包 |
| `test_imports.py` | 测试模块导入 |

### 其他文件（参考）

- `build.py` - 完整版（含 PyArmor 混淆）
- `build_simple.py` - 简化版
- `build_final.py` - 旧版本

## 打包配置

### xhs_helper.spec 已配置：

✅ **资源文件**：templates、static、config、resources、create_notes、xhs_nurturing  
✅ **隐藏导入**：所有必要的模块  
✅ **打包模式**：COLLECT（单目录，更稳定）  
✅ **压缩**：UPX 压缩  

## 打包输出

构建完成后，在 `release/` 目录生成：

### macOS
```
xhs_helper_darwin_arm64_v1.0.0.zip   # Apple Silicon
xhs_helper_darwin_x86_64_v1.0.0.zip  # Intel
```

### Windows
```
xhs_helper_windows_amd64_v1.0.0.zip
```

## 使用打包后的程序

### macOS

1. 解压 zip 文件
2. 进入 `xhs_helper/` 目录
3. 双击运行 `xhs_helper`
4. 浏览器会自动打开 http://127.0.0.1:5000

### Windows

1. 解压 zip 文件
2. 进入 `xhs_helper/` 目录
3. 双击运行 `xhs_helper.exe`
4. 浏览器会自动打开 http://127.0.0.1:5000

## 常见问题

### Q: 提示缺少模块？
A: 在 `xhs_helper.spec` 的 `hiddenimports` 中添加缺失的模块。

### Q: macOS 无法打开？
A: 右键点击 → 打开，或在系统偏好设置中允许。

### Q: 打包文件太大？
A: 在 `xhs_helper.spec` 的 `excludes` 中排除不需要的模块。

### Q: 如何添加代码混淆？
A: 安装 pyarmor 后使用 `build.py` 脚本。

## 测试导入

运行测试脚本检查模块：

```bash
python3 test_imports.py
```

应该显示：`22 成功, 0 失败` ✓

## 下一步

1. 测试打包后的程序功能
2. 在不同平台上验证
3. 更新版本号（在 spec 文件和脚本中）
4. 分发发布包
