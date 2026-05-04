"""api/knowledge/knowledge_service.py  ──  知识库文档解析/分块/检索/向量化服务"""
import os
import io
import uuid
import re
import asyncio
from datetime import datetime
from typing import List, Optional

import numpy as np

from backend.db_pg import get_conn, get_dict_cursor
from backend.storage import get_storage
from .embedding_service import embedding_service
from .vector_store import VectorStore, FAISS_AVAILABLE


class KnowledgeService:
    """知识库文档管理服务（支持 FAISS 向量检索）"""

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    STORAGE_PREFIX = "knowledge"
    SUPPORTED_TYPES = {".txt", ".md", ".pdf", ".docx"}

    def __init__(self):
        self._vector_stores: dict[int, VectorStore] = {}

    def _get_vector_store(self, user_id: int) -> Optional[VectorStore]:
        """获取或创建用户的 FAISS 向量存储"""
        if not FAISS_AVAILABLE or not embedding_service.available:
            return None
        if user_id not in self._vector_stores:
            vs = VectorStore(user_id)
            if vs.load():
                self._vector_stores[user_id] = vs
            else:
                vs.init_index(embedding_service.dimension)
                self._vector_stores[user_id] = vs
        return self._vector_stores[user_id]

    def _reset_vector_store(self, user_id: int):
        """重置用户的向量存储（重建索引用）"""
        vs = VectorStore(user_id)
        vs.init_index(embedding_service.dimension)
        self._vector_stores[user_id] = vs

    # ──── 文档 CRUD ────

    def create_document(
        self,
        user_id: int,
        filename: str,
        file_bytes: bytes,
        category: str = "help",
    ) -> dict:
        """上传并处理文档：存储 → 解析 → 分块 → 入库（向量化异步触发）"""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支持的文件类型: {ext}，支持: {', '.join(sorted(self.SUPPORTED_TYPES))}")

        doc_id = "doc_" + uuid.uuid4().hex[:16]
        file_size = len(file_bytes)

        # 1. 保存到对象存储
        storage = get_storage()
        remote_path = f"{self.STORAGE_PREFIX}/{user_id}/{doc_id}/{filename}"
        storage.save_bytes(file_bytes, remote_path)

        # 2. 解析 + 分块
        text = self._parse_text(file_bytes, ext)
        chunks = self._chunk_text(text)

        # 3. 写入 DB
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO t_knowledge_document
                   (doc_id, name, category, file_path, file_size, file_type, status, total_chunks, user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, 'completed', %s, %s)""",
                (doc_id, filename, category, remote_path, file_size, ext, len(chunks), user_id),
            )
            for idx, chunk_text in enumerate(chunks):
                chunk_id = "chk_" + uuid.uuid4().hex[:12]
                cur.execute(
                    """INSERT INTO t_knowledge_chunk (chunk_id, doc_id, content, chunk_index, token_count)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (chunk_id, doc_id, chunk_text, idx, len(chunk_text)),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            try:
                storage.delete(remote_path)
            except Exception:
                pass
            raise
        finally:
            cur.close()
            conn.close()

        return {
            "doc_id": doc_id,
            "name": filename,
            "category": category,
            "size": self._format_size(file_size),
            "chunks": len(chunks),
            "uploadTime": datetime.now().strftime("%Y-%m-%d"),
            "vectorized": False,
        }

    async def vectorize_document(self, user_id: int, doc_id: str) -> bool:
        """对指定文档的所有分块进行向量化并加入 FAISS 索引"""
        if not embedding_service.available:
            return False

        chunks = self.get_document_chunks(user_id, doc_id)
        if not chunks:
            return False

        chunk_ids = [c["chunk_id"] for c in chunks]
        texts = [c["content"] for c in chunks]

        # 生成 embedding
        vectors = await embedding_service.embed_texts(texts)
        normalized = embedding_service.normalize(vectors)

        # 加入 FAISS
        vs = self._get_vector_store(user_id)
        if vs is not None:
            vs.add(chunk_ids, normalized)

        # 更新 vector_id
        conn = get_conn()
        try:
            cur = conn.cursor()
            for chunk_id in chunk_ids:
                cur.execute(
                    "UPDATE t_knowledge_chunk SET vector_id = %s WHERE chunk_id = %s",
                    (f"faiss_{user_id}", chunk_id),
                )
            cur.execute(
                "UPDATE t_knowledge_document SET vectorized = TRUE WHERE doc_id = %s AND user_id = %s",
                (doc_id, user_id),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

        return True

    async def rebuild_user_index(self, user_id: int) -> int:
        """重建用户全部已向量化文档的 FAISS 索引"""
        if not embedding_service.available:
            return 0

        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            cur.execute(
                """SELECT chunk_id, content FROM t_knowledge_chunk
                   WHERE doc_id IN (SELECT doc_id FROM t_knowledge_document WHERE user_id = %s)
                   ORDER BY chunk_index""",
                (user_id,),
            )
            all_chunks = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        if not all_chunks:
            return 0

        self._reset_vector_store(user_id)
        vs = self._get_vector_store(user_id)
        if vs is None:
            return 0

        chunk_ids = [c["chunk_id"] for c in all_chunks]
        texts = [c["content"] for c in all_chunks]
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_ids = chunk_ids[i:i + batch_size]
            vectors = await embedding_service.embed_texts(batch_texts)
            normalized = embedding_service.normalize(vectors)
            vs.add(batch_ids, normalized)
            if i + batch_size < len(texts):
                await asyncio.sleep(0.2)

        # 标记所有文档为已向量化
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE t_knowledge_document SET vectorized = TRUE WHERE user_id = %s",
                (user_id,),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

        return len(chunk_ids)

    def list_documents(self, user_id: int) -> List[dict]:
        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            cur.execute(
                """SELECT doc_id, name, category, file_size, total_chunks, vectorized,
                          TO_CHAR(created_at, 'YYYY-MM-DD') AS upload_time
                   FROM t_knowledge_document
                   WHERE user_id = %s
                   ORDER BY created_at DESC""",
                (user_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r["doc_id"],
                    "name": r["name"],
                    "category": r["category"],
                    "size": self._format_size(r["file_size"] or 0),
                    "chunks": r["total_chunks"] or 0,
                    "uploadTime": r["upload_time"],
                    "vectorized": bool(r["vectorized"]),
                }
                for r in rows
            ]
        finally:
            cur.close()
            conn.close()

    def get_document(self, user_id: int, doc_id: str) -> Optional[dict]:
        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            cur.execute(
                """SELECT doc_id, name, category, file_size, total_chunks, vectorized, file_path,
                          TO_CHAR(created_at, 'YYYY-MM-DD') AS upload_time
                   FROM t_knowledge_document
                   WHERE doc_id = %s AND user_id = %s""",
                (doc_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row["doc_id"],
                "name": row["name"],
                "category": row["category"],
                "size": self._format_size(row["file_size"] or 0),
                "chunks": row["total_chunks"] or 0,
                "uploadTime": row["upload_time"],
                "vectorized": bool(row["vectorized"]),
                "file_path": row["file_path"],
            }
        finally:
            cur.close()
            conn.close()

    def get_document_chunks(self, user_id: int, doc_id: str) -> List[dict]:
        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            cur.execute(
                """SELECT c.chunk_id, c.content, c.chunk_index, c.token_count, c.vector_id
                   FROM t_knowledge_chunk c
                   JOIN t_knowledge_document d ON d.doc_id = c.doc_id
                   WHERE c.doc_id = %s AND d.user_id = %s
                   ORDER BY c.chunk_index""",
                (doc_id, user_id),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def delete_document(self, user_id: int, doc_id: str) -> bool:
        doc = self.get_document(user_id, doc_id)
        if not doc:
            return False

        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM t_knowledge_document WHERE doc_id = %s AND user_id = %s",
                (doc_id, user_id),
            )
            deleted = cur.rowcount
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

        # 从 FAISS 索引中移除（重建）
        if user_id in self._vector_stores:
            self._reset_vector_store(user_id)

        # 删除存储文件
        try:
            storage = get_storage()
            if doc.get("file_path"):
                storage.delete(doc["file_path"])
        except Exception:
            pass

        return deleted > 0

    # ──── 检索 ────

    async def search_documents(self, user_id: int, query: str, top_k: int = 5) -> List[dict]:
        """向量语义检索（FAISS），降级为关键词 ILIKE"""
        # 优先尝试 FAISS 向量检索
        vs = self._get_vector_store(user_id)
        if vs is not None and vs.count > 0 and embedding_service.available:
            try:
                query_vec = await embedding_service.embed_query(query)
                query_norm = embedding_service.normalize([query_vec])
                hits = vs.search(query_norm, top_k)
                if hits:
                    return self._resolve_search_results(hits)
            except Exception as e:
                print(f"[KnowledgeService] FAISS 检索失败，降级 ILIKE: {e}")

        # 降级：ILIKE 关键词匹配
        return self._search_ilike(user_id, query, top_k)

    def _resolve_search_results(self, hits: list) -> List[dict]:
        """根据 chunk_id 列表从 DB 获取 content 和 source"""
        chunk_ids = [h[0] for h in hits]
        score_map = dict(hits)
        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            cur.execute(
                """SELECT c.chunk_id, c.content, d.name AS source
                   FROM t_knowledge_chunk c
                   JOIN t_knowledge_document d ON d.doc_id = c.doc_id
                   WHERE c.chunk_id = ANY(%s)""",
                (chunk_ids,),
            )
            rows = {r["chunk_id"]: r for r in cur.fetchall()}
        finally:
            cur.close()
            conn.close()

        results = []
        for chunk_id, score in hits:
            row = rows.get(chunk_id)
            if row:
                results.append({
                    "content": row["content"][:300],
                    "source": row["source"],
                    "score": round(score, 4),
                })
        return results

    def _search_ilike(self, user_id: int, query: str, top_k: int) -> List[dict]:
        """降级方案：ILIKE 关键词匹配"""
        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            keywords = [k.strip() for k in re.split(r"\s+", query.strip()) if len(k.strip()) >= 1]
            if not keywords:
                return []
            conditions = " AND ".join(["c.content ILIKE %s" for _ in keywords])
            params = ["%" + kw + "%" for kw in keywords]
            cur.execute(
                f"""SELECT c.content, d.name AS source
                     FROM t_knowledge_chunk c
                     JOIN t_knowledge_document d ON d.doc_id = c.doc_id
                     WHERE d.user_id = %s AND {conditions}
                     LIMIT %s""",
                (user_id, *params, top_k),
            )
            rows = cur.fetchall()
            results = []
            for i, r in enumerate(rows):
                score = max(1.0 - i * 0.05, 0.5)
                results.append({
                    "content": r["content"][:300],
                    "source": r["source"],
                    "score": round(score, 4),
                })
            return results
        finally:
            cur.close()
            conn.close()

    # ──── 文本解析 ────

    def _parse_text(self, file_bytes: bytes, ext: str) -> str:
        if ext == ".pdf":
            return self._parse_pdf(file_bytes)
        elif ext == ".docx":
            return self._parse_docx(file_bytes)
        else:
            return self._parse_plain(file_bytes)

    def _parse_plain(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace")

    def _parse_pdf(self, file_bytes: bytes) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            texts = [p.extract_text() for p in reader.pages]
            return "\n\n".join(t for t in texts if t)
        except ImportError:
            raise RuntimeError("PDF 解析需要 PyPDF2 库，请运行: pip install PyPDF2")

    def _parse_docx(self, file_bytes: bytes) -> str:
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise RuntimeError("DOCX 解析需要 python-docx 库，请运行: pip install python-docx")

    # ──── 文本分块 ────

    def _chunk_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + self.CHUNK_SIZE
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.CHUNK_OVERLAP
            if start >= text_len:
                break
        return chunks

    # ──── 工具函数 ────

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


knowledge_service = KnowledgeService()
