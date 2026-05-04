# 存储架构文档目录

## 📁 文档列表

### 架构设计文档
- **STORAGE_ARCHITECTURE.md** - 完整存储架构设计文档（800+行）
  - 方案对比
  - 架构设计
  - 快速开始
  - API使用示例
  - 生产部署建议

### 实施报告
**位置**: `.context/STORAGE_REFACTOR_REPORT.md`
- 实施过程详细记录
- 技术决策说明
- 代码统计

### 测试报告
- **MINIO_TEST_SUCCESS.md** - MinIO测试成功报告
  - 测试结果
  - 配置说明
  - 使用示例

- **MINIO_INTEGRATION_COMPLETE.md** - API集成完成报告
  - dataset.py改造详情
  - 前后对比
  - 使用流程

- **STORAGE_DUAL_SUPPORT_CONFIRMED.md** - 双存储支持确认
  - 验证结果
  - 切换方法
  - 性能对比

## 🚀 快速导航

### 我想了解...

**存储架构设计** → [STORAGE_ARCHITECTURE.md](../STORAGE_ARCHITECTURE.md)

**如何使用MinIO** → [MINIO_TEST_SUCCESS.md](MINIO_TEST_SUCCESS.md)

**API如何集成** → [MINIO_INTEGRATION_COMPLETE.md](MINIO_INTEGRATION_COMPLETE.md)

**本地和MinIO对比** → [STORAGE_DUAL_SUPPORT_CONFIRMED.md](STORAGE_DUAL_SUPPORT_CONFIRMED.md)

**实施细节** → [../../.context/STORAGE_REFACTOR_REPORT.md](../.context/STORAGE_REFACTOR_REPORT.md)

## 📝 配置文件

**配置模板**: `../../.env.example`
**实际配置**: `../../.env` (不提交到Git)

### 配置说明

**.env.example** - 配置模板，包含所有可选项
- 提交到Git
- 供团队成员参考

**.env** - 实际使用的配置
- 不提交到Git（已在.gitignore中）
- 每个开发者本地配置

## 🔍 相关代码

**存储抽象层**: `../../backend/storage/`
- `__init__.py` - 工厂函数
- `base.py` - 抽象基类
- `local.py` - 本地文件系统
- `minio_storage.py` - MinIO对象存储

**应用集成**: 
- `../../backend/api/data/dataset.py` - 数据集管理API
- `../../backend/api/ml/model.py` - 模型管理API

## 📅 更新日志

- **2026-04-06**: 创建存储架构，完成MinIO集成

