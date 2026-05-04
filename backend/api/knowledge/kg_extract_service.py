"""KG triple extraction service with chunk dedup + extraction cache."""
import os
import json
import asyncio
import hashlib
from typing import List, Optional, Tuple

import httpx
from pydantic import BaseModel, field_validator

from backend.db_pg import get_conn, get_dict_cursor
from .graph_store import graph_store, VALID_ENTITY_TYPES, VALID_RELATION_TYPES


class Triple(BaseModel):
    subject_type: str
    subject_name: str
    relation_type: str
    object_type: str
    object_name: str
    confidence: float = 1.0

    @field_validator("subject_type", "object_type")
    @classmethod
    def validate_entity_type(cls, v):
        if v not in VALID_ENTITY_TYPES:
            closest = min(VALID_ENTITY_TYPES, key=lambda t: _edit_distance(v, t))
            return closest
        return v

    @field_validator("relation_type")
    @classmethod
    def validate_relation_type(cls, v):
        if v not in VALID_RELATION_TYPES:
            closest = min(VALID_RELATION_TYPES, key=lambda t: _edit_distance(v, t))
            return closest
        return v


def _edit_distance(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


EXTRACTION_SYSTEM_PROMPT = """你是一个知识图谱三元组抽取专家。
请从输入文本中抽取 JSON 数组格式的三元组，字段必须是：
subject_type, subject_name, relation_type, object_type, object_name, confidence。
如果无法抽取，返回 []。不要输出解释文字。"""


class KGExtractService:
    """LLM-based triple extraction service (relay/qwen) with cache support."""

    def __init__(self):
        self.relay_api_key = os.getenv("RELAY_API_KEY", "")
        self.relay_url = os.getenv("RELAY_API_URL", "https://www.openclaudecode.cn")
        self.relay_model = os.getenv("RELAY_MODEL", "gpt-4o-mini")
        self.qwen_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.qwen_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.qwen_model = os.getenv("QWEN_MODEL", "qwen-plus")
        self.default_service = os.getenv("CHAT_SERVICE", "relay")

    async def _call_relay(self, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.relay_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.relay_model,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.relay_url}/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_qwen(self, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.qwen_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.qwen_model,
            "input": {
                "messages": [
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ]
            },
            "parameters": {"temperature": 0.1, "max_tokens": 2000, "result_format": "message"},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.qwen_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["output"]["choices"][0]["message"]["content"]

    async def _call_llm(self, text: str, service: Optional[str] = None) -> str:
        svc = service or self.default_service
        if svc == "qwen" and self.qwen_api_key:
            return await self._call_qwen(text)
        if self.relay_api_key:
            return await self._call_relay(text)
        if self.qwen_api_key:
            return await self._call_qwen(text)
        raise RuntimeError("No LLM API key configured (RELAY_API_KEY or DASHSCOPE_API_KEY)")

    def _parse_triples(self, raw: str) -> List[Triple]:
        text = raw.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            arr = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
        triples: List[Triple] = []
        for item in arr:
            if not isinstance(item, dict):
                continue
            try:
                triples.append(Triple(**item))
            except Exception:
                continue
        return triples

    async def extract_from_text(self, text: str, service: Optional[str] = None) -> List[Triple]:
        if not text.strip():
            return []
        raw = await self._call_llm(text, service)
        return self._parse_triples(raw)

    @staticmethod
    def _chunk_hash(text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def _load_cached_chunk_triples(self, user_id: int, doc_id: str, chunk_hash: str) -> List[Triple]:
        conn = get_conn()
        cur = get_dict_cursor(conn)
        cur.execute(
            """
            SELECT subject_type, subject_name, relation_type, object_type, object_name, confidence
            FROM t_kg_extract_cache
            WHERE user_id = %s AND doc_id = %s AND chunk_hash = %s
            ORDER BY id ASC
            """,
            (user_id, doc_id, chunk_hash),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [Triple(**r) for r in rows]

    def _save_chunk_cache(self, user_id: int, doc_id: str, chunk_hash: str, triples: List[Triple]) -> None:
        if not triples:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM t_kg_extract_cache WHERE user_id = %s AND doc_id = %s AND chunk_hash = %s",
            (user_id, doc_id, chunk_hash),
        )
        for t in triples:
            cur.execute(
                """
                INSERT INTO t_kg_extract_cache
                (user_id, doc_id, chunk_hash, subject_type, subject_name, relation_type, object_type, object_name, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    doc_id,
                    chunk_hash,
                    t.subject_type,
                    t.subject_name,
                    t.relation_type,
                    t.object_type,
                    t.object_name,
                    t.confidence,
                ),
            )
        conn.commit()
        cur.close()
        conn.close()

    async def extract_from_chunks(
        self,
        chunks: List[str],
        user_id: int,
        doc_id: str,
        service: Optional[str] = None,
    ) -> int:
        all_triples: List[Triple] = []
        seen_hashes = set()
        llm_calls = 0
        cache_hits = 0

        for chunk in chunks:
            text = (chunk or "").strip()
            if not text:
                continue

            h = self._chunk_hash(text)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            triples: List[Triple] = []
            try:
                triples = self._load_cached_chunk_triples(user_id, doc_id, h)
            except Exception as e:
                print(f"[KGExtract] cache read failed: {e}")

            if triples:
                cache_hits += 1
                all_triples.extend(triples)
                continue

            try:
                triples = await self.extract_from_text(text, service)
                llm_calls += 1
            except Exception as e:
                print(f"[KGExtract] chunk extract failed: {e}")
                continue

            if triples:
                all_triples.extend(triples)
                try:
                    self._save_chunk_cache(user_id, doc_id, h, triples)
                except Exception as e:
                    print(f"[KGExtract] cache write failed: {e}")

            await asyncio.sleep(0.2)

        if not all_triples:
            print(f"[KGExtract] doc={doc_id} no triples. llm_calls={llm_calls}, cache_hits={cache_hits}")
            return 0

        triple_dicts = [t.model_dump() for t in all_triples]

        neo4j_count = 0
        if graph_store.available:
            try:
                neo4j_count = await graph_store.add_triples(user_id, doc_id, triple_dicts)
            except Exception as e:
                print(f"[KGExtract] Neo4j write failed: {e}")

        try:
            conn = get_conn()
            cur = conn.cursor()
            for t in all_triples:
                cur.execute(
                    """
                    INSERT INTO t_knowledge_triple
                    (doc_id, user_id, subject_type, subject_name, relation_type, object_type, object_name, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        doc_id,
                        user_id,
                        t.subject_type,
                        t.subject_name,
                        t.relation_type,
                        t.object_type,
                        t.object_name,
                        t.confidence,
                    ),
                )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[KGExtract] PostgreSQL write failed: {e}")

        print(
            f"[KGExtract] doc={doc_id} triples={len(all_triples)}, Neo4j={neo4j_count}, "
            f"llm_calls={llm_calls}, cache_hits={cache_hits}, unique_chunks={len(seen_hashes)}"
        )
        return len(all_triples)


kg_extract_service = KGExtractService()
