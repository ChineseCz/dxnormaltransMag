import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5432, database='dx_platform_db', user='dx_user', password='dx123456')
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
print("Tables:", [r[0] for r in cur.fetchall()])
conn.close()

