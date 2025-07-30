# 更新日志

本文档记录了 Layer Peel 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中的功能
- 支持更多压缩格式（LZMA、XZ等）
- 并行解压缩支持
- 进度条和取消操作支持
- 配置文件支持
- 插件系统

## [0.1.0] - 2024-01-XX

### 新增
- 🎉 首次发布 Layer Peel
- 🔄 递归解压缩多层嵌套压缩文件
- 📦 支持 ZIP、TAR、TGZ、7Z、RAR 格式
- 🚀 流式处理，内存友好
- 🎯 自动文件格式检测
- 🛡️ 完善的异常处理系统
- 🔧 命令行工具 `layer-peel`
- 📝 完整的 API 文档和使用示例
- 🧪 全面的测试覆盖
- 🌐 中文文档支持

### 核心功能
- **递归解压缩**: 自动处理嵌套的压缩文件，支持任意深度
- **多格式支持**:
  - ZIP 文件 (.zip)
  - TAR 归档 (.tar)
  - Gzip 压缩的 TAR (.tgz, .tar.gz)
  - 7-Zip 压缩 (.7z)
  - RAR 压缩 (.rar)
- **流式处理**: 使用迭代器模式，避免大文件内存溢出
- **智能检测**: 基于文件头自动识别压缩格式
- **编码处理**: 智能处理各种字符编码的文件名
- **错误恢复**: 遇到损坏文件时继续处理其他文件

### API 设计
- `extract()`: 主要的解压缩函数
- `get_mime_type()`: MIME 类型检测
- `fix_encoding()`: 文件名编码修复
- `read_stream()`: 流式文件读取
- 自定义异常类系统

### 命令行工具
- 基本解压缩功能
- 输出目录指定 (`-o/--output`)
- 递归深度控制 (`-d/--depth`)
- 静默模式 (`-q/--quiet`)
- 详细模式 (`-v/--verbose`)
- 块大小配置 (`--chunk-size`)

### 开发工具
- 完整的开发环境配置
- 代码质量工具集成 (Black, isort, flake8, mypy)
- 测试框架和覆盖率报告
- Pre-commit 钩子
- 持续集成配置

### 文档
- 详细的 README 文档
- API 参考文档
- 贡献指南
- 更新日志
- 使用示例和最佳实践

---

## 版本说明

### 语义化版本控制

我们使用语义化版本控制 (SemVer)：

- **主版本号 (MAJOR)**: 不兼容的 API 变更
- **次版本号 (MINOR)**: 向后兼容的功能新增
- **修订号 (PATCH)**: 向后兼容的问题修正

### 变更类型

- **新增 (Added)**: 新功能
- **变更 (Changed)**: 现有功能的变更
- **弃用 (Deprecated)**: 即将移除的功能
- **移除 (Removed)**: 已移除的功能
- **修复 (Fixed)**: Bug 修复
- **安全 (Security)**: 安全相关的修复

### 发布周期

- **主版本**: 根据需要发布，通常包含重大架构变更
- **次版本**: 每月发布，包含新功能和改进
- **修订版本**: 根据需要发布，主要用于 Bug 修复

---

## 贡献

如果您想为 Layer Peel 做出贡献，请查看我们的 [贡献指南](CONTRIBUTING.md)。

## 支持

如果您遇到问题或有建议，请：

- 📋 [提交 Issue](https://github.com/yourusername/layer-peel/issues)
- 💬 [参与讨论](https://github.com/yourusername/layer-peel/discussions)
- 📧 发送邮件到 contributors@layer-peel.dev
