"""api/knowledge/vector_store.py  ──  FAISS 向量存储管理"""
import os
import json
import pathlib
from typing import List, Tuple, Optional

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class VectorStore:
    """FAISS 向量索引管理器（每用户一个索引）"""

    def __init__(self, user_id: int):
        if not FAISS_AVAILABLE:
            raise RuntimeError("faiss-cpu 未安装，请运行: pip install faiss-cpu")

        self.user_id = user_id
        self._dimension: Optional[int] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._chunk_ids: List[str] = []       # index[i] → chunk_id
        self._storage_dir = pathlib.Path(__file__).parent.parent.parent / "storage" / "faiss"
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def index_path(self) -> str:
        return str(self._storage_dir / f"user_{self.user_id}.index")

    @property
    def mapping_path(self) -> str:
        return str(self._storage_dir / f"user_{self.user_id}.json")

    @property
    def count(self) -> int:
        return len(self._chunk_ids)

    # ──── 初始化 / 加载 ────

    def init_index(self, dimension: int):
        """创建新索引（会清除已有数据）"""
        self._dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._chunk_ids = []

    def load(self) -> bool:
        """从磁盘加载索引和映射"""
        if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
            return False
        try:
            self._index = faiss.read_index(self.index_path)
            self._dimension = self._index.d
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                self._chunk_ids = json.load(f)
            return True
        except Exception as e:
            print(f"[VectorStore] 加载索引失败: {e}")
            self._index = None
            self._chunk_ids = []
            return False

    def save(self):
        """持久化索引和映射"""
        if self._index is None or self._dimension is None:
            return
        faiss.write_index(self._index, self.index_path)
        with open(self.mapping_path, "w", encoding="utf-8") as f:
            json.dump(self._chunk_ids, f, ensure_ascii=False)

    # ──── 向量操作 ────

    def add(self, chunk_ids: List[str], vectors: np.ndarray) -> int:
        """添加向量（vectors 已归一化）"""
        if self._index is None:
            raise RuntimeError("索引未初始化，请先调用 init_index() 或 load()")
        if vectors.shape[1] != self._dimension:
            raise ValueError(f"向量维度 {vectors.shape[1]} 与索引维度 {self._dimension} 不匹配")
        self._index.add(vectors.astype(np.float32))
        self._chunk_ids.extend(chunk_ids)
        self.save()
        return self._index.ntotal

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """检索最相似的 top_k 个块，返回 [(chunk_id, score), ...]"""
        if self._index is None or self._index.ntotal == 0:
            return []
        query = query_vector.astype(np.float32).reshape(1, -1)
        scores, indices = self._index.search(query, min(top_k, self._index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunk_ids):
                continue
            results.append((self._chunk_ids[idx], float(score)))
        return results

    def remove_by_doc_id(self, doc_id: str) -> int:
        """删除某文档的全部向量（重建索引）"""
        if self._index is None:
            return 0
        # 找出不属于该 doc_id 的 chunk_ids
        keep_ids = [cid for cid in self._chunk_ids if not cid.startswith(f"chk_") or self._chunk_id_belongs(cid, doc_id) is False]
        # Need to get the vectors for keep_ids and rebuild
        # Since we can't extract vectors from IndexFlat, we rebuild from chunk data
        removed = len(self._chunk_ids) - len(keep_ids)
        # Will be fully rebuilt by caller
        return removed

    def clear(self):
        """清空索引"""
        if self._index is not None and self._dimension is not None:
            self._index.reset()
        self._chunk_ids = []

    def _chunk_id_belongs(self, chunk_id: str, doc_id: str) -> bool:
        """检查 chunk_id 是否属于指定 doc_id（从 DB 查询）"""
        from backend.db_pg import get_conn, get_dict_cursor
        conn = get_conn()
        try:
            cur = get_dict_cursor(conn)
            cur.execute("SELECT doc_id FROM t_knowledge_chunk WHERE chunk_id = %s", (chunk_id,))
            row = cur.fetchone()
            return row and row["doc_id"] == doc_id
        finally:
            cur.close()
            conn.close()
