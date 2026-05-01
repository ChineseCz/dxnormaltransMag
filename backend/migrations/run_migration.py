"""
数据库迁移脚本执行工具
"""
import os
import sys

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db_pg import get_conn

def run_migration(sql_file):
    """执行SQL迁移脚本"""
    print(f"正在执行迁移: {sql_file}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"[SUCCESS] Migration completed: {sql_file}")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrations_dir = os.path.dirname(__file__)
    migration_file = os.path.join(migrations_dir, '003_create_file_system.sql')

    if os.path.exists(migration_file):
        run_migration(migration_file)
    else:
        print(f"[ERROR] Migration file not found: {migration_file}")
