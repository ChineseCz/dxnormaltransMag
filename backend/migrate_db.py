"""一次性迁移脚本：为 t_dataset / t_dataset_file 补列，并将 datasets.json 数据导入 PG"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_pg import get_conn

def run():
    conn = get_conn()
    cur  = conn.cursor()

    # ── 1. DDL：补列 ──────────────────────────────────────────
    ddls = [
        "ALTER TABLE t_dataset ADD COLUMN IF NOT EXISTS data_org VARCHAR(32) DEFAULT 'multicolumn'",
        "ALTER TABLE t_dataset ADD COLUMN IF NOT EXISTS coord_system VARCHAR(16) DEFAULT 'xyz'",
        "ALTER TABLE t_dataset_file ADD COLUMN IF NOT EXISTS condition_value FLOAT DEFAULT NULL",
        "ALTER TABLE t_dataset_file ADD COLUMN IF NOT EXISTS storage_path VARCHAR(512) DEFAULT ''",
        "ALTER TABLE t_dataset_file ADD COLUMN IF NOT EXISTS upload_time_str VARCHAR(32) DEFAULT ''",
    ]
    for ddl in ddls:
        cur.execute(ddl)
        print(f"DDL OK: {ddl[:70]}")
    conn.commit()

    # ── 2. 迁移 datasets.json → t_dataset + t_dataset_file ──
    json_path = os.path.join(os.path.dirname(__file__), 'datasets', 'datasets.json')
    if not os.path.exists(json_path):
        print("datasets.json 不存在，跳过数据迁移")
        cur.close(); conn.close(); return

    with open(json_path, 'r', encoding='utf-8') as f:
        all_ds = json.load(f)

    imported = 0
    for ds in all_ds:
        try:
            cur.execute("""
                INSERT INTO t_dataset
                    (id, name, device_type, field_type, description,
                     input_variables, output_variable, time_step, coord_cols,
                     coord_system, data_org,
                     process_config, pipeline_status, train_info)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    name            = EXCLUDED.name,
                    pipeline_status = EXCLUDED.pipeline_status,
                    train_info      = EXCLUDED.train_info,
                    updated_at      = NOW()
            """, (
                ds['id'], ds.get('name',''), ds.get('deviceType','other'),
                ds.get('fieldType','other'), ds.get('description',''),
                json.dumps(ds.get('inputVariables',[])),
                json.dumps(ds.get('outputVariable',{})),
                ds.get('timeStep', 0.0005),
                ds.get('coordCols', 3),
                ds.get('coordSystem','xyz'),
                ds.get('dataOrg','multicolumn'),
                json.dumps(ds.get('processConfig',{})),
                json.dumps(ds.get('pipelineStatus',{'cut':False,'split':False,'zscore':False,'pca':False})),
                json.dumps(ds.get('trainInfo')) if ds.get('trainInfo') else None,
            ))

            for fobj in ds.get('files', []):
                cur.execute("""
                    INSERT INTO t_dataset_file
                        (dataset_id, filename, role, variable_index,
                         condition_value, file_size, analysis,
                         storage_path, upload_time_str)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """, (
                    ds['id'],
                    fobj.get('filename',''),
                    fobj.get('role','unknown'),
                    fobj.get('variableIndex'),
                    fobj.get('conditionValue'),
                    fobj.get('size', 0),
                    json.dumps(fobj.get('analysis',{'rows':0,'cols':0})),
                    fobj.get('storagePath',''),
                    fobj.get('uploadTime',''),
                ))
            imported += 1
        except Exception as e:
            print(f"  ⚠ 导入 {ds['id']} 失败: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close(); conn.close()
    print(f"\n✓ 迁移完成：{imported}/{len(all_ds)} 个数据集已写入 PostgreSQL")

if __name__ == '__main__':
    run()

