"""
db_setup_pg.py  ──  向 PostgreSQL dx_platform_db 写入初始用户数据
DDL（建表）已由 docker-compose 挂载 sql/pg/01_init_schema.sql 自动执行。
本脚本只负责插入角色 + bcrypt 加密用户（幂等，重复运行无副作用）。

运行方式：
  python backend/db_setup_pg.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from db_pg import get_conn, get_dict_cursor

ROLES = [
    (1, '超级管理员', '{"all": true}'),
    (2, '工程师',     '{"read": true, "predict": true}'),
    (3, '访客',       '{"read": true}'),
]

# bcrypt cost=10，与论文描述保持一致
USERS = [
    ('admin',  b'admin123',  1, '技术部'),
    ('user1',  b'user1pass', 2, '研发部'),
    ('tester', b'test1234',  2, '测试部'),
]


def init_pg():
    conn = get_conn()
    cur  = get_dict_cursor(conn)

    print("── 写入角色 ──")
    for role_id, role_name, perms in ROLES:
        cur.execute(
            """INSERT INTO t_role(id, role_name, permissions)
               VALUES(%s, %s, %s::jsonb)
               ON CONFLICT (id) DO NOTHING""",
            (role_id, role_name, perms),
        )
    print(f"  ✓ {len(ROLES)} 个角色写入完成")

    # 确保序列不冲突
    cur.execute("SELECT setval('t_role_id_seq', 10) WHERE (SELECT MAX(id) FROM t_role) < 10")

    print("\n── 写入用户（bcrypt cost=10，首次较慢）──")
    for username, pwd, role_id, dept in USERS:
        pw_hash = bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=10)).decode()
        cur.execute(
            """INSERT INTO t_user(username, password_hash, role_id, dept)
               VALUES(%s, %s, %s, %s)
               ON CONFLICT (username) DO NOTHING""",
            (username, pw_hash, role_id, dept),
        )
        print(f"  用户 {username!r} 已写入（bcrypt）")

    conn.commit()
    cur.close()

    # 验证
    with get_dict_cursor(conn) as c:
        c.execute("SELECT COUNT(*) AS cnt FROM t_user")
        n = c.fetchone()['cnt']
    conn.close()

    print(f"\n✓ PostgreSQL 初始化完成")
    print(f"  数据库 : dx_platform_db @ 127.0.0.1:5432")
    print(f"  用户数 : {n}")


if __name__ == "__main__":
    init_pg()

