# 项目目录结构整理说明

## 📁 当前目录结构

```
dxnormaltransMag/
├── .env                    # 实际配置（不提交Git）
├── .env.example            # 配置模板（提交Git）
├── .gitignore              # Git忽略规则
├── run.py                  # 后端启动脚本
│
├── backend/                # 后端代码
│   ├── api/               # API接口
│   ├── storage/           # 存储抽象层 ⭐
│   └── ...
│
├── frontend/              # 前端代码
│
├── tests/                 # 测试脚本 ⭐ 新增
│   ├── storage/          # 存储相关测试
│   │   ├── test_storage.py
│   │   ├── verify_storage.py
│   │   └── init_minio.py
│   └── README.md
│
├── docs/                  # 文档
│   ├── storage/          # 存储相关文档 ⭐ 新增
│   │   ├── STORAGE_ARCHITECTURE.md
│   │   ├── MINIO_TEST_SUCCESS.md
│   │   ├── MINIO_INTEGRATION_COMPLETE.md
│   │   ├── STORAGE_DUAL_SUPPORT_CONFIRMED.md
│   │   └── README.md
│   └── ...
│
├── .context/             # 会话上下文（不提交）
│   ├── SESSION_2026-04-05.md
│   ├── STORAGE_REFACTOR_REPORT.md
│   └── P1-2_MODEL_TRAIN_IMPLEMENTATION.md
│
└── env/                  # Docker环境配置
    └── docker-compose.yml
```

---

## 📝 配置文件说明

### .env vs .env.example

| 文件 | 用途 | 提交Git | 说明 |
|------|------|---------|------|
| `.env` | **实际配置** | ❌ 不提交 | 包含真实密钥，每个开发者本地配置 |
| `.env.example` | **配置模板** | ✅ 提交 | 不含密钥，供团队参考 |

### 为什么需要两个？

**团队协作场景**：
1. 新成员克隆代码
2. 复制 `.env.example` 为 `.env`
3. 根据本地环境修改配置
4. 不会把密钥提交到Git

**配置示例**：
```bash
# .env.example（模板，提交Git）
STORAGE_BACKEND=local
MINIO_ACCESS_KEY=minioadmin

# .env（实际，不提交）
STORAGE_BACKEND=minio
MINIO_ACCESS_KEY=my-real-secret-key
```

---

## 🗂️ 目录整理原则

### tests/ - 测试脚本
**放什么**：
- 单元测试
- 集成测试
- 功能验证脚本
- 初始化脚本

**不放什么**：
- 业务代码
- 配置文件

### docs/ - 文档
**放什么**：
- 架构设计文档
- 使用说明
- API文档
- 测试报告

**不放什么**：
- 代码文件
- 临时笔记

### .context/ - 会话上下文
**放什么**：
- 开发进度记录
- 技术决策文档
- 实施报告

**特点**：
- 不提交到Git（.gitignore已配置）
- 供AI助手恢复上下文

---

## 🧹 本次整理内容

### ✅ 已移动文件

**测试脚本** → `tests/storage/`
- test_storage.py
- verify_storage.py
- init_minio.py
- test_model_api.py

**文档** → `docs/storage/`
- MINIO_TEST_SUCCESS.md
- MINIO_INTEGRATION_COMPLETE.md
- STORAGE_DUAL_SUPPORT_CONFIRMED.md

### ✅ 新增说明文件
- tests/README.md
- docs/storage/README.md
- PROJECT_STRUCTURE.md（本文件）

---

## 📍 快速导航

### 我想...

**运行存储测试** → `python tests/storage/test_storage.py`

**查看存储文档** → `docs/storage/STORAGE_ARCHITECTURE.md`

**初始化MinIO** → `python tests/storage/init_minio.py`

**配置存储后端** → 修改 `.env` 文件

**查看配置模板** → `.env.example`

---

## 🔐 安全提醒

### ⚠️ 不要提交到Git的文件
- `.env` - 包含真实密钥
- `.context/` - 包含临时笔记
- `datasets/` - 数据文件太大
- `*.db` - 数据库文件
- `__pycache__/` - Python缓存

### ✅ 应该提交的文件
- `.env.example` - 配置模板
- `tests/` - 测试代码
- `docs/` - 文档
- `backend/` - 业务代码
- `frontend/` - 前端代码

---

## 📅 更新日志

- **2026-04-06**: 
  - 创建 tests/storage/ 目录
  - 创建 docs/storage/ 目录
  - 移动测试脚本和文档
  - 整理项目结构

---

**维护者**: dx-platform 开发团队  
**最后更新**: 2026-04-06

