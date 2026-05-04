"""api/assistant/routes.py  ──  智能助手问答接口"""
import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import uuid
from datetime import datetime

from .chat_service import ChatService
from backend.api.auth.jwt import get_current_user
from backend.db_pg import get_conn, get_dict_cursor

router = APIRouter()
chat_service = ChatService()


# ─────────────── Pydantic 模型 ───────────────

class Message(BaseModel):
    role: str       # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: str = "default"
    messages: List[Message]
    service: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = True
    rag_enabled: bool = False
    rag_top_k: int = 5
    kg_enabled: bool = True


class ConversationCreate(BaseModel):
    title: str = "新对话"


class ConversationRename(BaseModel):
    title: str


class MessageSave(BaseModel):
    conversation_id: str
    messages: List[Message]   # 追加保存的消息列表


# ─────────────── 中文关键词提取 ───────────────

import re as _re

_STOP_WORDS = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
               "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
               "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么", "如何", "请",
               "帮", "帮我", "进行", "分析", "给出", "建议", "通过", "使用", "以及", "并且",
               "可以", "能否", "是否", "目前", "当前", "其中", "对于", "关于", "以下"}


def _extract_chinese_keywords(text: str, max_kw: int = 8) -> list:
    """从中文文本中提取关键词（标点分割 + 停用词过滤）"""
    segments = _re.split(r'[，。、；：！？\s,.\-;:!?()（）""''【】\[\]{}]+', text)
    keywords = []
    for seg in segments:
        seg = seg.strip()
        if not seg or seg in _STOP_WORDS:
            continue
        if len(seg) <= 6:
            if seg not in _STOP_WORDS:
                keywords.append(seg)
        else:
            for i in range(0, len(seg) - 1, 2):
                chunk = seg[i:i + 3] if i + 3 <= len(seg) else seg[i:]
                if len(chunk) >= 2 and chunk not in _STOP_WORDS:
                    keywords.append(chunk)
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique[:max_kw]


# ─────────────── 对话流式接口 ───────────────

@router.post('/chat/stream')
async def chat_stream(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    """流式对话接口（支持 KG-RAG 双轨知识增强）"""
    if not body.messages:
        return JSONResponse(status_code=400, content={'error': '消息列表不能为空'})

    messages = [{"role": msg.role, "content": msg.content} for msg in body.messages]
    user_id = int(current_user['sub'])
    query = messages[-1]['content'] if messages else ''

    async def _dual_track_stream() -> AsyncGenerator[str, None]:
        route_info = None
        sources_info = {"kg": [], "vector": []}

        if body.rag_enabled and query:
            try:
                from backend.api.knowledge.intent_router import intent_router
                from backend.api.knowledge.knowledge_service import knowledge_service
                from backend.api.knowledge.graph_store import graph_store

                routing = await intent_router.classify(query)
                tracks = routing["tracks"]
                intent = routing["intent"]

                badges = []
                if "kg" in tracks:
                    badges.append({
                        "icon": "\U0001f578️", "label": "KG 图谱轨道",
                        "bg": "rgba(139,92,246,0.18)", "color": "#c084fc",
                        "border": "rgba(139,92,246,0.35)",
                    })
                if "vector" in tracks:
                    badges.append({
                        "icon": "\U0001f4c4", "label": "FAISS 向量轨道",
                        "bg": "rgba(59,130,246,0.18)", "color": "#60a5fa",
                        "border": "rgba(59,130,246,0.35)",
                    })
                if len(tracks) > 1:
                    badges.append({
                        "icon": "⚡", "label": "异步并发",
                        "bg": "rgba(251,191,36,0.12)", "color": "#fbbf24",
                        "border": "rgba(251,191,36,0.25)",
                    })

                tasks = {}
                if "kg" in tracks and body.kg_enabled and graph_store.available:
                    keywords = _extract_chinese_keywords(query)
                    if keywords:
                        tasks["kg"] = graph_store.search_paths(user_id, keywords, max_hops=4, limit=5)
                if "vector" in tracks:
                    tasks["vector"] = knowledge_service.search_documents(
                        user_id=user_id, query=query, top_k=body.rag_top_k,
                    )

                results = {}
                if tasks:
                    gathered = await asyncio.gather(
                        *[tasks[k] for k in tasks], return_exceptions=True
                    )
                    for key, result in zip(tasks.keys(), gathered):
                        if isinstance(result, Exception):
                            print(f"[RAG] {key} 检索失败: {result}")
                            results[key] = []
                        else:
                            results[key] = result or []

                kg_results = results.get("kg", [])
                vector_results = results.get("vector", [])

                sources_info["kg"] = kg_results
                sources_info["vector"] = [
                    {
                        "title": r.get("source", ""),
                        "excerpt": r.get("content", "")[:200],
                        "similarity": r.get("score", 0),
                    }
                    for r in vector_results
                ]

                route_info = {"badges": badges}

                yield json.dumps({
                    "type": "route",
                    "route": route_info,
                    "sources": sources_info,
                }, ensure_ascii=False) + "\n"

                context_parts = []
                if kg_results:
                    kg_text = "\n".join(
                        f"因果链路: {' → '.join(r['chain'])} (置信度: {r['confidence']})"
                        for r in kg_results
                    )
                    context_parts.append(f"【知识图谱检索结果】\n{kg_text}")
                if vector_results:
                    vec_text = "\n".join(
                        f"【来源: {r['source']}】{r['content']}"
                        for r in vector_results
                    )
                    context_parts.append(f"【向量知识库检索结果】\n{vec_text}")

                if context_parts:
                    rag_context = (
                        "以下是从知识库中检索到的相关参考内容（包含知识图谱因果链和向量文档），"
                        "请基于这些内容辅助回答用户问题。"
                        "如果参考内容与问题不相关，请忽略并正常回答。\n\n"
                        + "\n\n".join(context_parts)
                    )
                    insert_pos = 0
                    for i, m in enumerate(messages):
                        if m['role'] == 'system':
                            insert_pos = i + 1
                            break
                    messages.insert(insert_pos, {"role": "system", "content": rag_context})

            except Exception as e:
                print(f"[RAG] 双轨检索失败: {e}")
                import traceback
                traceback.print_exc()

        async for chunk in chat_service.chat_stream(
            messages=messages,
            service=body.service,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        ):
            yield chunk

    return StreamingResponse(
        _dual_track_stream(),
        media_type="text/event-stream",
    )


# ─────────────── 会话 CRUD ───────────────

@router.get('/conversations')
def list_conversations(current_user: dict = Depends(get_current_user)):
    """获取当前用户的所有会话（按更新时间倒序，最多50条）"""
    user_id = int(current_user['sub'])
    try:
        conn = get_conn()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at,
                   COUNT(m.id) AS message_count
            FROM t_ai_conversation c
            LEFT JOIN t_ai_message m ON m.conversation_id = c.id
            WHERE c.user_id = %s
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT 50
        """, (user_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {'conversations': [dict(r) for r in rows]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/conversations')
def create_conversation(body: ConversationCreate, current_user: dict = Depends(get_current_user)):
    """新建会话"""
    user_id = int(current_user['sub'])
    conv_id = 'conv_' + uuid.uuid4().hex[:16]
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO t_ai_conversation (id, user_id, title)
            VALUES (%s, %s, %s)
        """, (conv_id, user_id, body.title[:200]))
        conn.commit()
        cur.close(); conn.close()
        return {'id': conv_id, 'title': body.title, 'created_at': datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.put('/conversations/{conv_id}')
def rename_conversation(conv_id: str, body: ConversationRename, current_user: dict = Depends(get_current_user)):
    """重命名会话"""
    user_id = int(current_user['sub'])
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE t_ai_conversation SET title = %s, updated_at = NOW()
            WHERE id = %s AND user_id = %s
        """, (body.title[:200], conv_id, user_id))
        conn.commit()
        cur.close(); conn.close()
        return {'ok': True}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.delete('/conversations/{conv_id}')
def delete_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    """删除会话（级联删除消息）"""
    user_id = int(current_user['sub'])
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM t_ai_conversation WHERE id = %s AND user_id = %s", (conv_id, user_id))
        conn.commit()
        cur.close(); conn.close()
        return {'ok': True}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.get('/conversations/{conv_id}/messages')
def get_messages(conv_id: str, current_user: dict = Depends(get_current_user)):
    """获取会话的全部消息"""
    user_id = int(current_user['sub'])
    try:
        conn = get_conn()
        cur = get_dict_cursor(conn)
        # 先验证会话归属
        cur.execute("SELECT id FROM t_ai_conversation WHERE id = %s AND user_id = %s", (conv_id, user_id))
        if not cur.fetchone():
            cur.close(); conn.close()
            return JSONResponse(status_code=404, content={'error': '会话不存在'})

        cur.execute("""
            SELECT id, role, content, created_at
            FROM t_ai_message WHERE conversation_id = %s ORDER BY created_at ASC
        """, (conv_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {'messages': [dict(r) for r in rows]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/conversations/{conv_id}/messages')
def save_messages(conv_id: str, body: MessageSave, current_user: dict = Depends(get_current_user)):
    """批量追加消息并更新会话时间"""
    user_id = int(current_user['sub'])
    try:
        conn = get_conn()
        cur = conn.cursor()
        # 验证归属
        cur.execute("SELECT id FROM t_ai_conversation WHERE id = %s AND user_id = %s", (conv_id, user_id))
        if not cur.fetchone():
            cur.close(); conn.close()
            return JSONResponse(status_code=404, content={'error': '会话不存在'})

        for msg in body.messages:
            msg_id = 'm_' + uuid.uuid4().hex[:16]
            cur.execute("""
                INSERT INTO t_ai_message (id, conversation_id, role, content)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (msg_id, conv_id, msg.role, msg.content))

        cur.execute("UPDATE t_ai_conversation SET updated_at = NOW() WHERE id = %s", (conv_id,))
        conn.commit()
        cur.close(); conn.close()
        return {'ok': True, 'saved': len(body.messages)}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


# ─────────────── 健康检查 ───────────────

@router.get('/health')
def health():
    return {
        'status': 'ok',
        'services': {
            'qwen': bool(chat_service.qwen_api_key),
            'relay': bool(chat_service.relay_api_key)
        },
        'default_service': chat_service.default_service
    }


@router.get('/config')
def get_config():
    return {
        'services': ['qwen', 'relay'],
        'default_service': chat_service.default_service,
        'qwen_model': chat_service.qwen_model,
        'relay_model': chat_service.relay_model,
    }
