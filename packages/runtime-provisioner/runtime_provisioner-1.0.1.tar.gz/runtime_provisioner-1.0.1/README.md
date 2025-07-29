# Runtime Provisioner

运行时依赖自动下载器 - 一个用于自动下载和管理运行时依赖的Python库。

## 特性

- 🚀 **自动下载**: 导入时自动下载配置的依赖程序
- 🌍 **跨平台支持**: 支持 Windows、Linux、macOS
- 📦 **智能缓存**: 避免重复下载，支持版本管理
- 🔐 **安全可靠**: 解决常见的403错误，支持自定义请求头
- 📝 **简单易用**: 提供简洁的API接口

## 安装

```bash
pip install runtime-provisioner
```

## 快速开始

### 基本用法

```python
import runtime_provisioner

# 自动下载并获取Chrome 109
chrome_exe = runtime_provisioner.get_chrome_109_exe()
print(f"Chrome路径: {chrome_exe}")
```

### 使用说明

这个库目前主要用于自动下载Chrome 109浏览器：

```python
from runtime_provisioner import get_chrome_109_exe, Config

# 下载Chrome 109到默认位置
chrome_path = get_chrome_109_exe()

# 查看下载目录
print(f"下载目录: {Config.RUNTIME_PROVISION_DIR}")
```

### 配置

默认下载到用户目录下的 `runtime_provisioner` 文件夹：

```
~/runtime_provisioner/
├── Chrome109.zip    # 下载的压缩包
└── chrome.exe       # 解压后的可执行文件
```

## 技术特点

- 使用 `wget` 库进行文件下载
- 自动设置User-Agent避免403错误
- 支持ZIP文件自动解压
- 跨平台路径处理

## 常见问题

### Q: 下载失败怎么办？
A: 库已内置了User-Agent设置来避免403错误。如果仍有问题，请检查网络连接。

### Q: 如何清理下载的文件？
A: 删除 `~/runtime_provisioner` 目录即可。

### Q: 支持其他程序下载吗？
A: 目前专注于Chrome 109，后续版本会支持更多程序。

## 许可证

MIT License

## 支持的平台

- ✅ Windows
- ✅ Linux  
- ✅ macOS

## 更新日志

### 1.0.0
- 初始版本
- 支持Chrome 109自动下载
- 解决wget 403错误问题 