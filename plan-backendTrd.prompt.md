# 后端 TRD 技术方案设计 — 面向网络安全的智能化物理场预测平台

## 概要

当前后端基于 Flask 单进程 + JSON 文件存储。前端已完成 **5 大模块 15+ 页面**（数据集管理、数据处理、模型架构/训练/评估、实时预测/结果/对比/历史、AI 助手/知识库/Agent）。后端仅实现了数据集 CRUD 和数据处理流水线——**模型训练、实时预测、AI 助手、用户认证** 均为 stub 占位。本方案将后端重构为生产级架构，覆盖存储层、计算层、接口层、AI 层四大维度。

---

## 一、现状问题分析

| 维度 | 现状 | 问题 |
|------|------|------|
| **框架** | Flask 单进程 `debug=True` | 无法处理并发、无异步支持、训练阻塞主线程 |
| **存储** | `datasets.json` 文件读写 | 无事务、并发读写不安全、无索引查询 |
| **认证** | `user.py` 硬编码两个用户 | 无 JWT/Session、无 RBAC 鉴权 |
| **训练** | `model.py` `/train` 返回 stub 字符串 | 无异步任务队列、无进度推送、无 GPU 调度 |
| **预测** | `predict.py` `/realtime` 返回硬编码数组 | 未对接模型加载、归一化、逆 PCA 全链路 |
| **AI** | 前端 `useAiStore.js` 调用 `/api/ai/chat` | 后端无此蓝图、无 LLM/RAG 实现 |
| **计算** | `core_algorithms/` 下脚本硬编码路径 | 未封装为可参数化的 Service 层 |

---

## 二、目标架构

```text
+------------ Nginx / Caddy（反向代理 + 静态文件）-----------+
|  Vue3 前端  <->  REST API + WebSocket (SSE)                 |
+-------------------------------------------------------------+
|              Flask -> FastAPI（ASGI 异步）                    |
|  +----------+  +----------+  +---------+  +----------+      |
|  | 认证模块  |  | 数据集   |  | 模型    |  | AI 模块   |     |
|  | Auth     |  | Dataset  |  | Model   |  | AI       |      |
|  +----+-----+  +----+-----+  +----+----+  +----+-----+      |
|       |             |             |             |             |
|  +----+-------------+-------------+-------------+-----+      |
|  |              Service 层（业务逻辑）                  |      |
|  +----------+----------+----------+-------------------+      |
|             |          |          |                           |
|  +----------+--+ +-----+----+ +--+-----------+               |
|  | SQLite/PG   | | Redis    | | Celery       |               |
|  | （元数据）   | | （缓存）  | | （异步任务） |               |
|  +-------------+ +----------+ +--------------+               |
|           文件系统: datasets/<id>/...                         |
+-------------------------------------------------------------+
|  core_algorithms 计算层（PyTorch / sklearn / numpy）          |
|  + FAISS 向量库（RAG 知识检索）                               |
+-------------------------------------------------------------+
```

---

## 三、详细实施步骤

### 步骤 1：框架迁移 —— Flask 迁移至 FastAPI

- 将 `server.py` 迁移为 FastAPI `app` + `APIRouter`，保留现有 5 个蓝图对应的 router（`/api/user`、`/api/data`、`/api/dataset`、`/api/model`、`/api/predict`），新增 `/api/ai` router
- 引入 **Pydantic v2** 做请求/响应 Schema 校验（替代手动 `request.json.get(...)`）
- 使用 FastAPI 原生 `BackgroundTasks` / SSE（`sse-starlette`）支持训练进度流式推送和 AI 聊天流式输出
- 部署使用 `uvicorn`（ASGI）替代 Flask 内置 WSGI server，配合 `gunicorn -k uvicorn.workers.UvicornWorker` 多 worker 生产部署

### 步骤 2：存储层升级 —— JSON 迁移至 SQLAlchemy + SQLite/PostgreSQL

- 引入 **SQLAlchemy 2.0**（async session）+ **Alembic** 做数据库迁移管理
- 核心表结构设计：
  - `users` —— id, username, password_hash, role, dept, created_at
  - `datasets` —— id, name, device_type, field_type, description, input_variables(JSON), output_variable(JSON), time_step, process_config(JSON), pipeline_status(JSON), train_info(JSON), created_at, updated_at
  - `dataset_files` —— id, dataset_id(FK), filename, role, variable_index, size, analysis(JSON), upload_time
  - `models` —— id, dataset_id(FK), model_type, file_path, config(JSON), metrics(JSON), status, created_at
  - `training_jobs` —— id, model_id(FK), status(queued/running/done/failed), progress, logs(TEXT), started_at, finished_at
  - `predictions` —— id, dataset_id(FK), model_id(FK), inputs(JSON), field_values(BLOB/path), stats(JSON), created_at
  - `ai_conversations` —— id, user_id(FK), title, created_at
  - `ai_messages` —— id, conversation_id(FK), role, content, timestamp
  - `knowledge_docs` —— id, filename, category, chunk_count, embedding_status, uploaded_at
- 开发阶段使用 **SQLite** 零部署依赖，生产环境切换为 **PostgreSQL**
- 保留现有 `datasets/<id>/raw|data|pca_result|model|result` 文件目录结构，仅元数据入库
- 编写数据迁移脚本，将现有 `datasets.json` 一次性导入数据库

### 步骤 3：用户认证与权限 —— JWT + RBAC

- 在 `user.py` 基础上实现完整认证体系：
  - 密码采用 **bcrypt** 哈希存储
  - 登录签发 **JWT** access_token（`python-jose` 或 `PyJWT`），配合 `refresh_token` 实现无感续签
  - FastAPI `Depends()` 全局注入 `current_user`，按角色（超级管理员/管理员/普通用户）做路由级权限校验
- 对接前端 `UserManagement.vue`、`RoleManagement.vue`、`DeptManagement.vue` 的 CRUD 接口

### 步骤 4：模型训练服务 —— Celery 异步任务 + WebSocket/SSE 进度推送

- 引入 **Celery** + **Redis** 作为分布式任务队列（Redis 同时充当 broker 和 result backend）
- 将 `core_algorithms/modeltrain/` 下的脚本（`DNNtrain.py`、`CNNtrain.py`、`DNNportal.py` 等）封装为参数化的 Service 类，接受前端传入的架构配置（层结构、学习率、batch_size、epochs 等，对应 `ModelArchitecture.vue` 的 `savedConfig`）
- **动态模型构建**：根据前端 `dnnConfig.hiddenLayers`、`cnnConfig.convLayers`、`lstmConfig.layers` JSON 动态组装 `nn.Module`，而非硬编码 `NetShortCircuit`
- 训练任务 API 设计：
  - `POST /api/model/train` → 创建 Celery task，返回 `job_id`
  - `GET /api/model/train/{job_id}/stream` → SSE 端点，逐 epoch 推送 `{epoch, trainLoss, testLoss, lr}`，替换前端当前的 `setInterval` 模拟
  - `POST /api/model/train/{job_id}/stop` → 发送 `revoke` 信号终止训练
- 模型保存至 `datasets/<id>/model/<type>_<timestamp>.pth`，元数据写入 `models` 表
- ML 模型（SVM/RF/XGBoost）同理，使用 Celery task 包装 sklearn `fit()`，支持交叉验证进度回报

### 步骤 5：实时预测服务 —— 全链路推理管线

- 重写 `predict.py` 实现完整推理流程：
  1. 根据 `dataset_id` 加载该数据集的 `zstrainmuInput.txt`（μ）和 `zstrainsigmaInput.txt`（σ）
  2. 对前端传入的原始输入做 Z-Score 归一化：`x_norm = (x - μ) / σ`
  3. 根据 `model_file` 从 `models` 表获取模型类型和配置，动态构建网络并加载 `state_dict`
  4. GPU/CPU 推理得到 PCA 系数向量
  5. 加载 `pca_result/mean_pca.txt` 和 `vector_pca.txt`，逆 PCA 还原为全空间场值
  6. 加载 `data/coordinates.txt` 作为坐标数据
  7. 计算统计指标（max、min、mean、std）
  8. 返回 `{fieldValues, coordinates, stats, pcaDim}` 给前端 `usePredictionStore.js`
- **模型热缓存**：使用 `functools.lru_cache` 或 Redis 缓存已加载模型权重，避免每次请求重新 `torch.load`
- `POST /api/predict/batch` —— 批量工况预测（多组输入一次返回），对接 `PredictCompare.vue`
- `GET /api/predict/history` —— 从数据库查询历史预测记录，对接 `PredictHistory.vue`

### 步骤 6：AI 助手服务 —— LLM + RAG + Agent

- 新增 `/api/ai` 路由模块，对接前端 `useAiStore.js` 调用的所有端点：
  - **`POST /api/ai/chat`**：
    - 接入 **OpenAI API** 或兼容接口（如本地 Ollama/vLLM）
    - 构建 system prompt 注入平台上下文（当前数据集信息、最近预测结果等）
    - 使用 FastAPI `StreamingResponse` + SSE 实现流式 token 输出
    - 对话历史持久化到 `ai_conversations` + `ai_messages` 表
  - **`POST /api/ai/knowledge/upload`** + **`GET /api/ai/knowledge/list`** + **`DELETE /api/ai/knowledge/{id}`**：
    - 文档上传后使用 **LangChain** `TextSplitter` 分块
    - 使用 **sentence-transformers** 或 OpenAI Embeddings 生成向量
    - 存入 **FAISS** 本地向量索引（轻量，无需额外服务），索引文件持久化到磁盘
  - **`POST /api/ai/knowledge/search`**：RAG 检索，返回 Top-K 相关文档片段，注入 LLM prompt
  - **`POST /api/ai/agent/execute`**：
    - 实现工具调用能力（如自动执行数据处理、触发训练、查询预测结果）
    - 使用 LangChain Agent / OpenAI Function Calling 风格

---

## 四、技术选型汇总

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| Web 框架 | **FastAPI** + Uvicorn | 原生 async、自动 OpenAPI 文档、Pydantic 校验 |
| ORM | **SQLAlchemy 2.0** + Alembic | Python 生态最成熟 ORM，支持 async |
| 数据库 | SQLite（开发）→ **PostgreSQL**（生产） | 零部署开发、生产级扩展 |
| 缓存/消息 | **Redis** | Celery broker + 模型缓存 + session 存储 |
| 任务队列 | **Celery** | 训练任务异步执行、GPU worker 隔离、任务监控 |
| 认证 | **JWT**（PyJWT）+ bcrypt | 无状态、前后端分离友好 |
| AI/LLM | **OpenAI SDK** / Ollama 本地 | 灵活切换云端/私有化部署 |
| RAG 向量库 | **FAISS** + sentence-transformers | 轻量、无服务依赖、适合中小规模知识库 |
| ML/DL | **PyTorch** + sklearn（现有） | 保持不变，仅封装为 Service |

---

## 五、待确认事项

1. **LLM 选型**：使用 OpenAI API（GPT-4o）快速落地，还是使用 Ollama + Qwen2.5 本地私有化部署？前者开发快但有网络依赖和数据外泄风险，后者需 GPU 资源但完全离线。**建议：双模式 config 切换**。

2. **训练任务 GPU 调度**：当前是否只有单 GPU？如果多卡或多机，是否需要引入 Ray Serve / Kubernetes Job 进行调度？**单机阶段建议 Celery + 单 GPU worker，后期再考虑分布式**。

3. **数据库选型确认**：开发阶段用 SQLite 零部署成本最低，但如果需要多人同时使用（如演示或教学场景），建议直接上 PostgreSQL Docker 容器。**是否有 Docker 环境可用？**

4. **API 版本管理**：迁移过程中是否需要保持旧 Flask 接口兼容一段时间（`/api/v1` + `/api/v2` 双版本），还是前后端同步一次性切换？
