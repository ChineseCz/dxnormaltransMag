import psycopg2, json
conn = psycopg2.connect(host='127.0.0.1', port=5432, database='dx_platform_db', user='dx_user', password='dx123456')
cur = conn.cursor()
cur.execute("SELECT id, model_type, config, metrics FROM t_model WHERE status='done' ORDER BY created_at DESC LIMIT 5")
for r in cur.fetchall():
    mid, mtype, cfg, metrics = r
    if isinstance(cfg, str):
        try: cfg = json.loads(cfg)
        except: pass
    if isinstance(metrics, str):
        try: metrics = json.loads(metrics)
        except: pass
    idim = metrics.get('input_dim') if isinstance(metrics, dict) else '?'
    odim = metrics.get('output_dim') if isinstance(metrics, dict) else '?'
    print(f"id={mid} type={mtype} input_dim={idim} output_dim={odim}")
    print(f"  config={cfg}")
conn.close()

