# 项目进展报告

> 报告生成时间：2026-04-03
> 项目名称：面向网络安全的智能化物理场预测平台

---

## 一、项目概览

本项目旨在构建一个面向电力装备（变压器、电抗器、高压套管等）的智能化物理场预测与可视化服务平台，融合深度学习（DNN/CNN）、PCA 降维、知识图谱检索增强生成（KG-RAG）等技术，最终目标为五层微服务架构全栈落地。

---

## 二、整体架构目标（AGENTS.md）

```
表现层（Vue3 + ECharts + AI Agent 面板）
      ↕ HTTP RESTful / WebSocket
接入与网关层（Nginx + FastAPI + WebSocket）
      ↕
微服务业务逻辑层（RBAC 鉴权 / 数据流水线 / 模型版本管理 / LangChain RAG）
      ↕
分布式调度与计算层（Redis/RabbitMQ + Celery + CPU/GPU Worker + 推理引擎）
      ↕
数据持久化层（PostgreSQL + Redis 缓存 + 分布式文件系统 + FAISS 向量库）
```

---

## 三、当前各模块完成状态

### 3.1 后端服务（Flask + Python）

| 模块 | 文件 | 状态 | 说明 |
|------|------|:----:|------|
| 应用入口 | `server.py` | 完成 | Flask + CORS，注册 9 个 Blueprint，支持 waitress 生产启动 |
| 用户鉴权 | `api/user.py` | 基本完成 | bcrypt 密码哈希、MySQL/SQLite 双模式自动切换、异步审计日志 |
| 数据集管理 | `api/dataset.py` | 完成 | 完整 CRUD + 文件上传/删除/角色修改 + 四步处理流水线（截取/划分/归一化/PCA）|
| 数据处理 | `api/data.py` | 完成 | 原始数据上传、稳态自动检测、处理状态查询 |
| 模型管理 | `api/model.py` | Stub | 仅列出 .pth 文件列表；训练接口返回占位字符串，**未接入真实训练** |
| 实时预测 | `api/predict.py` | 部分完成 | 真实仿真场数据读取与 3D 可视化已实现；`/realtime` 为模拟延迟占位 |
| AI 助手 | `api/ai.py` | Stub | 返回预置答案 + 模拟 LLM 延迟，**未接入真实 LLM / RAG** |
| 高压套管场 | `api/gaoya.py` | 完成 | 238,222 节点，100~5000A 电流档位，分层采样，内存缓存 |
| 电抗器场 | `api/reactor.py` | 完成 | 91,462 节点，100A，支持 r-z 截面 + 三维回转可视化 |
| 变压器电场 | `api/transfield.py` | 完成 | 139,067 节点，多电压档位，电场/电位双类型，分层采样 |

### 3.2 数据库层

| 组件 | 文件 | 状态 | 说明 |
|------|------|:----:|------|
| SQLite 初始化 | `db_setup.py` | 完成 | t_user / t_role / t_audit_log，bcrypt 预置3用户 |
| MySQL 初始化 | `db_setup_mysql.py` | 完成 | 同结构 MySQL 版本，含 53 个压测用户（worker001~050）|
| MySQL 连接池 | `db_mysql.py` | 完成 | DBUtils PooledDB，max=30，blocking=True，自动 ping |
| 双模式切换 | `api/user.py` | 完成 | 环境变量 DB_MODE=sqlite 可强制 SQLite，MySQL 不可用时自动降级 |
| 数据集元数据 | `datasets/datasets.json` | 运行中 | JSON 文件持久化（待迁移至数据库） |

### 3.3 前端（Vue3 + ECharts + Element Plus）

技术栈：Vue 3.5 + Pinia 3 + Vue-Router 5 + ECharts 5 + ECharts-GL + Element Plus + Tailwind CSS 4

| 模块 | 页面数 | 完成状态 |
|------|:------:|:--------:|
| 认证（Login / Register）| 2 | 完成 |
| 用户中心（用户 / 角色 / 部门管理）| 3 | 完成 |
| 数据中心（数据集管理 / 上传 / 处理）| 3 | 完成 |
| 模型训练（架构 / 任务 / 评估 / 管理）| 4 | 完成 |
| 预测与可视化（配置 / 结果 / 对比 / 历史 / 高压套管 / 电抗器 / 变压器）| 7 | 完成 |
| AI 助手（对话 / 知识库 / Agent）| 3 | 完成 |
| 仪表盘 Dashboard | 1 | 完成 |
| **合计** | **23** | — |

公共组件：`Dashboard.vue` / `ChatDrawer.vue` / `DatasetSelector.vue` / `Scatter2DField.vue` / `WebGL3DScatter.vue`

状态管理：`useAuthStore.js` / `usePredictionStore.js` / `useAiStore.js`

路由守卫：已实现 token 校验 + 未登录重定向。

### 3.4 核心算法层（core_algorithms/）

| 子模块 | 状态 | 说明 |
|--------|:----:|------|
| 数据预处理流水线 | 完成 | 稳态截取 → 训练/测试划分 → Z-Score 归一化 → PCA 降维，全部封装为可调 API |
| DNN / CNN 模型训练脚本 | 完成（独立脚本）| 已有训练好的 .pth 模型文件；尚未封装为后端 Service |
| PCA 逆变换推理 | 完成（脚本层）| mean_pca.txt + vector_pca.txt 还原全空间场值 |
| KG-RAG 实验框架 | 基本完成 | 51 题（A/B/C 各 17 题）+ LLM-as-Judge 三指标自动评分（CR / F / AR）|
| FAISS 知识库 | 完成（脚本层）| 11 份文档常量已写入 run_experiment.py |
| 实验结果 Excel | 待生成 | 需 API Key 运行 `python run_experiment.py` |

---

## 四、压测结果摘要

- **工具**：自研压测脚本（`stress_test.py`）
- **目标接口**：`POST /api/user/login`（MySQL + bcrypt(cost=10) + 审计日志）
- **并发规模**：500 VU，预热 120s，持续 300s
- **稳定吞吐量**：约 **74 req/s**
- **中位响应时间**：约 **1.3 s**（主要瓶颈为 bcrypt 哈希验证）
- **成功率**：**100%**

> 实时预测接口（`/api/predict/realtime`）当前为模拟延迟（均值约 3.2s），待接入真实 PyTorch 推理后重新压测。

---

## 五、待完成工作（优先级排序）

### P0 — 核心功能补全

| 编号 | 任务 | 涉及文件 |
|------|------|---------|
| P0-1 | **模型训练接口真实化**：将 `core_algorithms/modeltrain/` 脚本封装为参数化 Service，接入 `api/model.py` | `api/model.py`，新增 `services/train_service.py` |
| P0-2 | **实时预测全链路**：Z-Score 归一化 → 模型加载 → PyTorch 推理 → 逆 PCA → 返回场值 | `api/predict.py`，`services/infer_service.py` |
| P0-3 | **AI 助手真实化**：接入 Qwen API 或本地 Ollama，实现流式输出 + 对话历史持久化 | `api/ai.py`，`services/rag_service.py` |

### P1 — 工程质量提升

| 编号 | 任务 | 说明 |
|------|------|------|
| P1-1 | **JWT 鉴权替换**：当前 token 为 SHA256 哈希，无过期校验；替换为 PyJWT + refresh_token | `api/user.py` |
| P1-2 | **异步任务队列**：引入 Celery + Redis，将训练任务移出主线程，支持进度 SSE 推送 | 新增 `celery_app.py`，`tasks/train_task.py` |
| P1-3 | **数据集元数据迁移**：将 `datasets.json` 迁移至 SQLAlchemy + SQLite/PostgreSQL | `api/dataset.py`，新增 `models/dataset_model.py` |
| P1-4 | **FastAPI 迁移**：替换 Flask，启用原生 async + SSE + Pydantic 校验 | `server.py` 及所有 blueprint |

### P2 — 论文实验收尾

| 编号 | 任务 | 说明 |
|------|------|------|
| P2-1 | 修复 `run_experiment.py` 中 `judge_faithfulness` 的多余 `__wrapped__` 行 | `core_algorithms/run_experiment.py` |
| P2-2 | `实验.md` 从四指标（CP/CR/F/AR）改为三指标（CR/F/AR），删除所有 CP 相关内容 | `core_algorithms/实验.md` |
| P2-3 | 运行完整实验生成 `experiment_result.xlsx`（需 DASHSCOPE_API_KEY）| `core_algorithms/run_experiment.py` |

---

## 六、目录结构速查

```
dxnormaltransMag/
├── server.py                  # Flask 应用入口（9 个 Blueprint）
├── db_mysql.py                # MySQL 连接池（DBUtils PooledDB）
├── db_setup.py                # SQLite schema 初始化
├── db_setup_mysql.py          # MySQL schema 初始化 + 53 个测试用户
├── requirements.txt           # 依赖（待补全）
├── stress_test.py             # 并发压测脚本
├── api/                       # REST API Blueprint 层
│   ├── user.py                # 用户鉴权（MySQL/SQLite 双模式）
│   ├── dataset.py             # 数据集 CRUD + 四步处理流水线
│   ├── data.py                # 原始数据上传与预处理
│   ├── model.py               # 模型列表（训练为 Stub）
│   ├── predict.py             # 场数据可视化 + 实时预测（Stub）
│   ├── ai.py                  # AI 问答（Mock）
│   ├── gaoya.py               # 高压套管功率损耗密度场
│   ├── reactor.py             # 电抗器轴对称磁场
│   └── transfield.py          # 变压器油纸套管电场/电位
├── core_algorithms/           # 算法核心层
│   ├── preprocess/            # 数据预处理脚本
│   ├── modeltrain/            # DNN/CNN 训练脚本
│   ├── model/                 # 已训练 .pth 模型文件
│   ├── data/                  # 处理后数据（PCA / Z-Score）
│   ├── run_experiment.py      # KG-RAG 实验框架（51题 + LLM-as-Judge）
│   └── PROGRESS.md            # 算法实验进度备忘
├── datasets/                  # 数据集目录（JSON 元数据 + 文件）
│   ├── datasets.json
│   ├── ds_5b9d4909/
│   └── ds_9e9e8331/
└── frontend/                  # Vue3 前端
    ├── src/
    │   ├── views/             # 23 个页面（auth/user/data/model/prediction/assistant）
    │   ├── components/        # 公共组件（WebGL 散点图、2D 散点图等）
    │   ├── composables/       # Pinia 状态仓库
    │   └── router.js          # 路由配置 + 导航守卫
    └── package.json           # Vue3 + ECharts + Element Plus + Tailwind
```

---

## 七、技术债务与风险提示

1. **`datasets.json` 并发写入不安全**：多请求同时写文件存在竞态，高并发下需迁移至数据库。
2. **Token 无过期机制**：当前 SHA256 token 无法撤销和过期，建议尽快替换 JWT。
3. **训练/预测主线程阻塞**：Flask 单进程下长耗时任务会阻塞所有请求，Celery 任务队列为必要升级项。
4. **requirements.txt 不完整**：仅包含 numpy / scikit-learn，未列出 Flask / bcrypt / pymysql 等实际依赖，部署时需补全。
5. **前端 API Key 硬编码风险**：如涉及 LLM API Key，需通过后端代理转发，不能暴露在前端代码中。

---

*本报告基于 2026-04-03 代码快照自动整理，如有更新请重新生成。*

