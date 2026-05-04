# CLAUDE.md — dx-platform 电磁场预测平台

## 项目概述
基于 FastAPI + Vue 3 的电气设备电磁场实时预测平台，支持 DNN/CNN/RF 模型训练、预测，以及 KG-RAG 双轨知识增强 AI 助手。

## 技术栈
- **后端**: FastAPI + psycopg2 (PooledDB) + Celery + Redis
- **前端**: Vue 3 (Composition API `<script setup>`) + Element Plus + Tailwind CSS
- **数据库**: PostgreSQL 16 (主业务) + Neo4j 5 (知识图谱)
- **存储**: MinIO (S3 兼容对象存储)
- **AI**: Relay (OpenAI 兼容) + Qwen (DashScope) 双 LLM 后端
- **向量**: FAISS IndexFlatIP + sentence-transformers (BAAI/bge-small-zh-v1.5, 512维)

## 目录结构
```
backend/
  main.py                          # FastAPI 入口，注册 11 个 router
  db_pg.py                         # PostgreSQL 连接池 (PooledDB)
  api/
    auth/routes.py, jwt.py         # JWT 鉴权
    assistant/routes.py            # AI 对话 (chat_stream 双轨 SSE)
    assistant/chat_service.py      # LLM 流式调用 (Qwen + Relay)
    knowledge/routes.py            # 知识库 + 图谱 API
    knowledge/knowledge_service.py # 文档解析/分块/FAISS 检索
    knowledge/embedding_service.py # 本地 embedding (sentence-transformers)
    knowledge/vector_store.py      # FAISS 索引管理 (per-user)
    knowledge/graph_store.py       # Neo4j 图谱存储与多跳检索
    knowledge/kg_extract_service.py# LLM 三元组抽取
    knowledge/intent_router.py     # 意图路由 (关键词规则 + LLM)
    ml/model.py, predict.py        # 模型训练与预测
    data/routes.py, dataset.py     # 数据管理
  storage/                         # MinIO/Local 存储抽象
  migrations/                      # SQL 迁移脚本 (001-006)
frontend/src/
  composables/useAiStore.js        # AI 模块共享状态 (非 Pinia)
  views/assistant/AiChat.vue       # 对话页 (双轨 sources 展示)
  views/assistant/AiKnowledge.vue  # 知识库管理 (文档 + 图谱 tab)
env/
  docker-compose.yml               # PG/Redis/MinIO/Neo4j/Nacos 等
  requirements.txt                 # Python 依赖
```

## 关键架构模式
- **路由注册**: `app.include_router(router, prefix="/api/xxx")`
- **鉴权**: `Depends(get_current_user)` 返回 `{"sub": user_id}`
- **DB 操作**: `get_conn()` 获取连接，手动 commit/close
- **异步**: `loop.run_in_executor()` 包装 CPU 密集操作，`BackgroundTasks` 异步处理
- **SSE 流式**: JSON Lines 格式 `{"type":"route|content|done", ...}`
- **前端状态**: Vue composable 单例模式，localStorage 持久化
- **前端 API**: 直接 fetch，token 从 localStorage 读取

## KG-RAG 双轨架构
```
用户提问 → 意图路由 (intent_router) → asyncio.gather 并发:
  ├─ KG 轨道: graph_store.search_paths() → Neo4j 多跳路径
  └─ 向量轨道: knowledge_service.search_documents() → FAISS
→ SSE 先发 {"type":"route", badges, sources}
→ 再流式输出 LLM 回答
```

## 常用命令
```bash
# 后端启动
cd backend && python run.py

# 前端启动
cd frontend && npm run dev

# Docker 基础设施
cd env && docker-compose up -d postgres redis minio neo4j
```

## 环境变量 (.env)
关键变量: PG_HOST/PORT/USER/PASSWORD/DB, REDIS_HOST, MINIO_ENDPOINT,
NEO4J_URI/USER/PASSWORD, RELAY_API_KEY/URL/MODEL, DASHSCOPE_API_KEY, CHAT_SERVICE
