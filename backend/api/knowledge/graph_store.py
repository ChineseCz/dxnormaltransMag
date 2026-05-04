"""Neo4j graph store for knowledge graph triples."""
import os
import asyncio
from typing import List, Optional

from neo4j import GraphDatabase

VALID_ENTITY_TYPES = {
    "Device", "Component", "Phenomenon", "Fault_Cause", "Solution",
    "Model_Type", "Training_Metric", "Algorithm_Issue", "Hyperparam_Tuning",
}

VALID_RELATION_TYPES = {
    "HAS_PART", "SHOWS_ABNORM", "INDICATES", "REQUIRES",
    "EVALUATED_BY", "EXHIBITS", "MITIGATED_BY",
}


class GraphStore:
    """Lazy-initialized Neo4j graph store."""

    def __init__(self):
        self._driver = None
        self._available: Optional[bool] = None
        self._last_check: float = 0

    def _lazy_init(self):
        import time

        now = time.time()
        if self._available is not None and (self._available or now - self._last_check < 30):
            return

        self._last_check = now
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j123")

        try:
            if self._driver:
                try:
                    self._driver.close()
                except Exception:
                    pass

            self._driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                notifications_disabled_classifications=["UNRECOGNIZED", "UNSUPPORTED", "GENERIC"],
            )
            self._driver.verify_connectivity()
            self._available = True
            print(f"[GraphStore] Neo4j connected: {uri}")
        except Exception as e:
            self._driver = None
            self._available = False
            print(f"[GraphStore] Neo4j connect failed: {e}")

    @property
    def available(self) -> bool:
        if self._available is None:
            self._lazy_init()
        return self._available or False

    def close(self):
        if self._driver:
            self._driver.close()

    async def add_triples(self, user_id: int, doc_id: str, triples: List[dict]) -> int:
        """Write triples and attach source doc_id into relationship/node doc_ids arrays."""
        if not self.available or not triples:
            return 0

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_write, user_id, doc_id, triples)

    def _execute_write(self, user_id: int, doc_id: str, triples: List[dict]) -> int:
        with self._driver.session() as session:
            query = """
            UNWIND $triples AS t
            MERGE (s {name: t.subject_name, type: t.subject_type, user_id: $user_id})
            MERGE (o {name: t.object_name, type: t.object_type, user_id: $user_id})
            MERGE (s)-[r:RELATES {rel_type: t.relation_type, user_id: $user_id}]->(o)
            SET r.confidence = coalesce(t.confidence, 1.0),
                r.doc_ids = CASE
                    WHEN r.doc_ids IS NULL THEN [$doc_id]
                    WHEN NOT $doc_id IN r.doc_ids THEN r.doc_ids + $doc_id
                    ELSE r.doc_ids
                END,
                s.doc_ids = CASE
                    WHEN s.doc_ids IS NULL THEN [$doc_id]
                    WHEN NOT $doc_id IN s.doc_ids THEN s.doc_ids + $doc_id
                    ELSE s.doc_ids
                END,
                o.doc_ids = CASE
                    WHEN o.doc_ids IS NULL THEN [$doc_id]
                    WHEN NOT $doc_id IN o.doc_ids THEN o.doc_ids + $doc_id
                    ELSE o.doc_ids
                END
            RETURN count(r) AS cnt
            """
            result = session.run(query, triples=triples, user_id=user_id, doc_id=doc_id)
            row = result.single()
            return int(row["cnt"] if row else 0)

    async def search_paths(
        self, user_id: int, query_keywords: List[str], max_hops: int = 4, limit: int = 5
    ) -> List[dict]:
        if not self.available or not query_keywords:
            return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_search, user_id, query_keywords, max_hops, limit)

    def _execute_search(self, user_id: int, keywords: List[str], max_hops: int, limit: int) -> List[dict]:
        with self._driver.session() as session:
            clean_kw = [k.strip() for k in keywords if k.strip()]
            if not clean_kw:
                return []

            where_clauses = " OR ".join(f"start.name CONTAINS $kw{i}" for i in range(len(clean_kw)))
            kw_params = {f"kw{i}": k for i, k in enumerate(clean_kw)}

            query = f"""
            MATCH (start {{user_id: $user_id}})
            WHERE {where_clauses}
            OPTIONAL MATCH path = (start)-[*1..{min(max_hops, 6)}]->(end)
            WHERE ALL(n IN nodes(path) WHERE n.user_id = $user_id)
            WITH path, start,
                 CASE WHEN path IS NOT NULL THEN nodes(path) ELSE [start] END AS ns,
                 CASE WHEN path IS NOT NULL THEN relationships(path) ELSE [] END AS rs,
                 CASE WHEN path IS NOT NULL AND SIZE(relationships(path)) > 0
                      THEN REDUCE(c = 0.0, r IN relationships(path) | c + coalesce(r.confidence, 1.0)) / SIZE(relationships(path))
                      ELSE 1.0 END AS avg_conf
            ORDER BY avg_conf DESC, SIZE(ns) ASC
            LIMIT $limit
            RETURN
                [n IN ns | {{name: n.name, type: n.type}}] AS chain_nodes,
                [r IN rs | {{rel_type: r.rel_type, confidence: r.confidence, doc_ids: coalesce(r.doc_ids, [])}}] AS chain_rels,
                avg_conf AS confidence
            """

            result = session.run(query, user_id=user_id, limit=limit, **kw_params)
            paths = []
            for record in result:
                nodes = record["chain_nodes"]
                rels = record["chain_rels"]
                conf = record["confidence"]
                paths.append(
                    {
                        "chain": [n["name"] for n in nodes],
                        "chain_nodes": nodes,
                        "chain_rels": rels,
                        "confidence": f"{conf * 100:.1f}%" if conf else "N/A",
                    }
                )
            return paths

    async def delete_by_doc(self, user_id: int, doc_id: str) -> int:
        """Source-aware deletion: remove doc_id source, delete only empty relationships."""
        if not self.available:
            return 0

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_delete_doc, user_id, doc_id)

    def _execute_delete_doc(self, user_id: int, doc_id: str) -> int:
        with self._driver.session() as session:
            # 1) remove doc source from relationships
            session.run(
                """
                MATCH ()-[r:RELATES {user_id: $user_id}]->()
                WHERE r.doc_ids IS NOT NULL AND $doc_id IN r.doc_ids
                SET r.doc_ids = [d IN r.doc_ids WHERE d <> $doc_id]
                """,
                user_id=user_id,
                doc_id=doc_id,
            )

            # 2) delete relationships that lost all sources
            result = session.run(
                """
                MATCH ()-[r:RELATES {user_id: $user_id}]->()
                WHERE r.doc_ids IS NULL OR size(r.doc_ids) = 0
                DELETE r
                RETURN count(r) AS cnt
                """,
                user_id=user_id,
            )
            row = result.single()
            deleted_rels = int(row["cnt"] if row else 0)

            # 3) remove doc source from nodes
            session.run(
                """
                MATCH (n {user_id: $user_id})
                WHERE n.doc_ids IS NOT NULL AND $doc_id IN n.doc_ids
                SET n.doc_ids = [d IN n.doc_ids WHERE d <> $doc_id]
                """,
                user_id=user_id,
                doc_id=doc_id,
            )

            # 4) cleanup isolated nodes
            session.run(
                """
                MATCH (n {user_id: $user_id})
                WHERE NOT (n)--()
                DELETE n
                """,
                user_id=user_id,
            )

            return deleted_rels

    async def get_stats(self, user_id: int) -> dict:
        if not self.available:
            return {"entities": 0, "relations": 0, "available": False}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_stats, user_id)

    def _execute_stats(self, user_id: int) -> dict:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (n {user_id: $user_id})
                WITH count(n) AS entity_count
                OPTIONAL MATCH ()-[r:RELATES {user_id: $user_id}]->()
                RETURN entity_count, count(r) AS relation_count
                """,
                user_id=user_id,
            )
            record = result.single()
            return {
                "entities": record["entity_count"],
                "relations": record["relation_count"],
                "available": True,
            }


graph_store = GraphStore()
