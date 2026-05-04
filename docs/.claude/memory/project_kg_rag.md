---
name: KG-RAG 双轨架构进度
description: Phase 4 知识图谱与双轨 KG-RAG 的实现状态、已完成步骤和待验证项
type: project
---

Phase 4 KG-RAG 双轨混合检索架构已于 2026-05-03 完成代码实现。

**Why:** 将单轨 FAISS-RAG 升级为论文中的 KG-RAG 双轨架构，提升故障诊断场景的上下文召回率（论文数据：A 类 CR 从 0.39 提升到 0.72）。

**已完成：**
- Step 1: Neo4j 5 加入 docker-compose，neo4j 驱动已安装，环境变量已配置
- Step 2: graph_store.py — Neo4j 连接管理、MERGE 写入、CONTAINS 中文关键词多跳检索
- Step 3: kg_extract_service.py — LLM Few-Shot 三元组抽取（用户后续增加了 chunk 去重 + 抽取缓存 t_kg_extract_cache 表）
- Step 4: intent_router.py — 关键词规则 + LLM 兜底分类，所有类型都走双轨
- Step 5: assistant/routes.py 双轨调度 — asyncio.gather 并发，SSE 先发 route/sources 再流式内容
- Step 6: 前端适配 — useAiStore.js 解析 route SSE，AiKnowledge.vue 新增图谱 tab
- 数据库: t_knowledge_triple 表已建，t_kg_extract_cache 表由用户后续添加

**How to apply:** 后续开发应基于此双轨架构扩展，不要回退到单轨 RAG。新增知识库功能时注意同时考虑向量和图谱两条轨道。
