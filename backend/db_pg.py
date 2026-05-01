"""
db_pg.py  ──  PostgreSQL 共享连接池（psycopg2 + DBUtils PooledDB）
配置来源：环境变量 / .env 文件

  PG_HOST      默认 127.0.0.1
  PG_PORT      默认 5432
  PG_USER      默认 dx_user
  PG_PASSWORD  默认 dx123456
  PG_DB        默认 dx_platform_db
"""
import os
import threading
import psycopg2
import psycopg2.extras

PG_CFG = dict(
    host     = os.environ.get("PG_HOST",     "127.0.0.1"),
    port     = int(os.environ.get("PG_PORT", "5432")),
    user     = os.environ.get("PG_USER",     "dx_user"),
    password = os.environ.get("PG_PASSWORD", "dx123456"),
    dbname   = os.environ.get("PG_DB",       "dx_platform_db"),
)

_pool      = None
_pool_lock = threading.Lock()


def _build_pool():
    global _pool
    try:
        from dbutils.pooled_db import PooledDB
        _pool = PooledDB(
            creator        = psycopg2,
            mincached      = 2,
            maxcached      = 10,
            maxconnections = 20,
            blocking       = True,
            ping           = 1,
            **PG_CFG,
        )
        print("[db_pg] PooledDB OK (max=20 connections)")
    except ImportError:
        print("[db_pg] DBUtils 未安装，降级为每次请求新建连接")
        _pool = None


def get_conn():
    """获取连接。调用者负责 close()。"""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _build_pool()
    if _pool is not None:
        return _pool.connection()
    return psycopg2.connect(**PG_CFG)


def get_dict_cursor(conn):
    """返回一个 RealDictCursor，结果行支持 row['column'] 访问。"""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def test_connection() -> bool:
    try:
        conn = get_conn()
        with get_dict_cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM t_user")
            row = cur.fetchone()
        conn.close()
        print(f"[db_pg] PostgreSQL OK — t_user: {row['cnt']} 行")
        return True
    except Exception as e:
        print(f"[db_pg] PostgreSQL FAIL: {e}")
        return False


if __name__ == "__main__":
    test_connection()

