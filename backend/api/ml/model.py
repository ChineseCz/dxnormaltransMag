"""api/ml/model.py  ──  模型训练接口（已接入真实训练逻辑）"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, threading, json

from backend.db_pg import get_conn
from backend.api.auth.jwt import get_current_user

router = APIRouter()

_HERE        = os.path.dirname(os.path.abspath(__file__))    # api/ml/
_BACKEND     = os.path.dirname(os.path.dirname(_HERE))        # backend/
ROOT_DIR     = os.path.dirname(_BACKEND)                      # project root
DATASETS_DIR = os.path.join(_BACKEND, 'datasets')             # backend/datasets/（与 dataset.py 保持一致）


class TrainRequest(BaseModel):
    dataset_id:    str   = ""
    model_type:    str   = "DNN"    # DNN / CNN / RF
    epochs:        int   = 3000
    batch_size:    int   = 16
    learning_rate: float = 1e-4
    # DNN 架构（来自前端 dnnConfig.hiddenLayers）
    hidden_layers: list  = []       # [16, 32, 64]
    # CNN 架构
    conv_layers:   list  = []       # [{filters,kernel_size,pooling}, ...]
    fc_units:      int   = 256
    # RF 超参数
    n_estimators:       int   = 100
    max_depth:          int   = 20
    min_samples_split:  int   = 2
    min_samples_leaf:   int   = 1
    max_features:       str   = "sqrt"
    bootstrap:          bool  = True
    oob_score:          bool  = False


class TrainConfig(BaseModel):
    config: dict = {}


# ========== 全局训练任务追踪 ==========
_training_jobs = {}  # {job_id: {"status": str, "progress": int, "logs": list}}


@router.get('/list')
def list_models(current_user: dict = Depends(get_current_user)):
    """列出所有已训练的模型"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.dataset_id, m.model_type, m.file_path, m.config, 
                   m.metrics, m.status, m.created_at, d.name as dataset_name
            FROM t_model m
            LEFT JOIN t_dataset d ON m.dataset_id = d.id
            ORDER BY m.created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        models = []
        for row in rows:
            models.append({
                "id": row[0],
                "dataset_id": row[1],
                "dataset_name": row[8],
                "model_type": row[2],
                "file_path": row[3],
                "config": row[4],
                "metrics": row[5],
                "status": row[6],
                "created_at": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None
            })

        return {"models": models, "total": len(models)}
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


@router.post('/train')
def train_model(body: TrainRequest, current_user: dict = Depends(get_current_user)):
    """触发模型训练（DNN / CNN → PyTorch；RF → scikit-learn）"""
    try:
        mtype = body.model_type.upper()

        # 1. 验证数据集
        dataset_dir = os.path.join(DATASETS_DIR, body.dataset_id)
        data_dir    = os.path.join(dataset_dir, 'data')
        model_dir   = os.path.join(dataset_dir, 'model')

        if not os.path.exists(dataset_dir):
            return JSONResponse(status_code=404, content={"error": f"数据集不存在: {body.dataset_id}"})

        required_files = ['zstrainInput.txt', 'zstestInput.txt', 'trainPCA.txt', 'testPCA.txt']
        # 回退检查：如果 zscore/PCA 文件不存在，降级用原始 split 文件（兼容旧数据集）
        fallback = not all(os.path.isfile(os.path.join(data_dir, f)) for f in required_files)
        if fallback:
            required_files = ['trainInput.txt', 'trainOutput.txt', 'testInput.txt', 'testOutput.txt']
        missing = [f for f in required_files if not os.path.isfile(os.path.join(data_dir, f))]
        if missing:
            return JSONResponse(status_code=400, content={
                "error": "数据集未完成预处理",
                "missing_files": missing,
                "hint": "请先完成数据集的 cut 和 split 步骤"
            })

        # 2. 创建模型记录
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO t_model (dataset_id, model_type, status, config)
            VALUES (%s, %s, 'training', %s) RETURNING id
        """, (body.dataset_id, mtype, json.dumps({
            "epochs": body.epochs, "batch_size": body.batch_size,
            "learning_rate": body.learning_rate,
            "hidden_layers": body.hidden_layers,
            "conv_layers":   body.conv_layers,
            "fc_units":      body.fc_units,
            "n_estimators":  body.n_estimators,
            "max_depth":     body.max_depth,
        })))
        model_id = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()

        # 3. 后台训练线程
        def _train_worker():
            import tempfile, shutil
            job_key = f"model_{model_id}"
            _training_jobs[job_key] = {"status": "running", "progress": 0, "logs": []}

            def progress_cb(epoch, train_loss, test_loss):
                total = body.epochs if mtype != "RF" else body.n_estimators
                _training_jobs[job_key]["progress"] = int(epoch / total * 100)
                _training_jobs[job_key]["current_epoch"] = epoch
                _training_jobs[job_key]["logs"].append(
                    f"Epoch {epoch}/{total} - Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}"
                )

            # 从存储层（MinIO 或本地）拉取数据文件到临时目录
            try:
                from backend.storage import get_storage
                storage = get_storage()
                use_storage = True
            except Exception:
                use_storage = False

            tmp_data_dir = None
            tmp_model_dir = None
            actual_data_dir = data_dir
            actual_model_dir = model_dir

            if use_storage:
                tmp_root = tempfile.mkdtemp(prefix=f"train_{model_id}_")
                tmp_data_dir  = os.path.join(tmp_root, "data")
                tmp_model_dir = os.path.join(tmp_root, "model")
                tmp_pca_dir   = os.path.join(tmp_root, "pca_result")
                os.makedirs(tmp_data_dir,  exist_ok=True)
                os.makedirs(tmp_model_dir, exist_ok=True)
                os.makedirs(tmp_pca_dir,   exist_ok=True)

                # 优先拉 zscore+PCA 文件，回退原始 split 文件
                data_files = [
                    'zstrainInput.txt', 'zstestInput.txt', 'trainPCA.txt', 'testPCA.txt',
                    'trainInput.txt', 'trainOutput.txt', 'testInput.txt', 'testOutput.txt',
                    'zstrainmuInput.txt', 'zstrainsigmaInput.txt',
                ]
                pca_files = ['mean_pca.txt', 'vector_pca.txt', 'variance_pca.txt']

                pulled = []
                for fname in data_files:
                    remote = f"datasets/{body.dataset_id}/data/{fname}"
                    local  = os.path.join(tmp_data_dir, fname)
                    try:
                        storage.load_file(remote, local)
                        pulled.append(fname)
                    except Exception:
                        src = os.path.join(data_dir, fname)
                        if os.path.exists(src):
                            shutil.copy2(src, local)
                            pulled.append(fname)

                for fname in pca_files:
                    remote = f"datasets/{body.dataset_id}/pca_result/{fname}"
                    local  = os.path.join(tmp_pca_dir, fname)
                    try:
                        storage.load_file(remote, local)
                    except Exception:
                        pca_dir_local = os.path.join(dataset_dir, 'pca_result')
                        src = os.path.join(pca_dir_local, fname)
                        if os.path.exists(src):
                            shutil.copy2(src, local)

                # 判断是否有足够文件
                has_zscore_pca = all(f in pulled for f in ['zstrainInput.txt', 'trainPCA.txt'])
                has_raw_split  = all(f in pulled for f in ['trainInput.txt', 'trainOutput.txt'])
                if has_zscore_pca or has_raw_split:
                    actual_data_dir  = tmp_data_dir
                    actual_model_dir = tmp_model_dir
                else:
                    shutil.rmtree(tmp_root, ignore_errors=True)
                    tmp_data_dir = tmp_model_dir = None
                    use_storage = False

            try:
                if mtype == "RF":
                    from .train_utils import train_rf_model
                    result = train_rf_model(
                        data_dir=actual_data_dir, model_save_dir=actual_model_dir,
                        n_estimators=body.n_estimators, max_depth=body.max_depth,
                        min_samples_split=body.min_samples_split,
                        min_samples_leaf=body.min_samples_leaf,
                        max_features=body.max_features,
                        bootstrap=body.bootstrap, oob_score=body.oob_score,
                        progress_callback=progress_cb,
                    )
                else:
                    from .train_utils import train_dnn_model
                    hl = []
                    for l in body.hidden_layers:
                        hl.append(l['units'] if isinstance(l, dict) else int(l))
                    cl = []
                    for l in body.conv_layers:
                        cl.append({
                            'filters':     l.get('filters', 32),
                            'kernel_size': l.get('kernelSize', l.get('kernel_size', 3)),
                            'pooling':     l.get('pooling', False),
                        })
                    result = train_dnn_model(
                        data_dir=actual_data_dir, model_save_dir=actual_model_dir,
                        model_type=mtype,
                        epochs=body.epochs, batch_size=body.batch_size, lr=body.learning_rate,
                        progress_callback=progress_cb,
                        hidden_layers=hl or None,
                        conv_layers=cl or None,
                        fc_units=body.fc_units,
                    )

                # 把模型文件推送到存储层（MinIO 或本地）
                model_filename = result['model_filename']
                remote_model_path = f"datasets/{body.dataset_id}/model/{model_filename}"
                if use_storage and tmp_model_dir:
                    local_model_file = os.path.join(tmp_model_dir, model_filename)
                    try:
                        storage.save_file(local_model_file, remote_model_path)
                        # 同时复制一份到本地 model 目录（保证本地可用）
                        os.makedirs(model_dir, exist_ok=True)
                        shutil.copy2(local_model_file, os.path.join(model_dir, model_filename))
                    except Exception as e_upload:
                        _training_jobs[job_key]["logs"].append(f"[WARN] 模型推送 MinIO 失败: {e_upload}")
                        shutil.copy2(local_model_file, os.path.join(model_dir, model_filename))
                else:
                    # 本地存储，result['model_path'] 已在 model_dir 下
                    pass

                # 更新数据库
                # 从 logs 解析 loss 历史曲线，持久化到 DB
                import re as _re
                loss_history = {"epochs": [], "train": [], "test": []}
                for line in _training_jobs[job_key].get("logs", []):
                    m = _re.match(r"Epoch\s+(\d+)/\d+\s*-\s*Train Loss:\s*([\d.eE+\-]+),\s*Test Loss:\s*([\d.eE+\-]+)", line)
                    if m:
                        loss_history["epochs"].append(int(m.group(1)))
                        loss_history["train"].append(float(m.group(2)))
                        loss_history["test"].append(float(m.group(3)))

                conn2 = get_conn(); cur2 = conn2.cursor()
                cur2.execute("""
                    UPDATE t_model SET status='done', file_path=%s, metrics=%s WHERE id=%s
                """, (
                    remote_model_path,
                    json.dumps({
                        "final_train_loss":     result['final_train_loss'],
                        "final_test_loss":      result['final_test_loss'],
                        "final_train_loss_pca": result.get('final_train_loss_pca'),
                        "final_test_loss_pca":  result.get('final_test_loss_pca'),
                        "inverse_transform_ok": result.get('inverse_transform_ok', False),
                        "input_dim":  result['input_dim'],
                        "output_dim": result['output_dim'],
                        "loss_history": loss_history,
                        "used_pca":    os.path.exists(os.path.join(actual_data_dir, 'trainPCA.txt')),
                        "used_zscore": os.path.exists(os.path.join(actual_data_dir, 'zstrainInput.txt')),
                        "pca_path":    f"datasets/{body.dataset_id}/pca_result",
                        "zscore_mu_path":    f"datasets/{body.dataset_id}/data/zstrainmuInput.txt",
                        "zscore_sigma_path": f"datasets/{body.dataset_id}/data/zstrainsigmaInput.txt",
                    }),
                    model_id,
                ))
                conn2.commit(); cur2.close(); conn2.close()

                _training_jobs[job_key].update({"status": "done", "progress": 100, "result": result})

            except Exception as e:
                import traceback
                _training_jobs[job_key].update({
                    "status": "failed", "error": str(e), "trace": traceback.format_exc()
                })
                conn2 = get_conn(); cur2 = conn2.cursor()
                cur2.execute("UPDATE t_model SET status='failed' WHERE id=%s", (model_id,))
                conn2.commit(); cur2.close(); conn2.close()
            finally:
                # 清理临时目录
                if tmp_data_dir:
                    shutil.rmtree(os.path.dirname(tmp_data_dir), ignore_errors=True)

        threading.Thread(target=_train_worker, daemon=True).start()

        return {
            "status": "started", "model_id": model_id,
            "job_key": f"model_{model_id}",
            "message": f"{mtype} 训练已启动",
            "hint": f"GET /api/model/train/status/{model_id} 查询进度"
        }

    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


@router.get('/train/status/{model_id}')
def get_train_status(model_id: int, current_user: dict = Depends(get_current_user)):
    """查询训练任务状态"""
    job_key = f"model_{model_id}"

    # 查询数据库状态
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status, metrics, created_at FROM t_model WHERE id = %s", (model_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return JSONResponse(status_code=404, content={"error": "模型不存在"})

    db_status, metrics, created_at = row

    # 如果有实时任务信息，优先返回
    if job_key in _training_jobs:
        job = _training_jobs[job_key]
        return {
            "model_id": model_id,
            "status": job["status"],
            "progress": job["progress"],
            "current_epoch": job.get("current_epoch", 0),
            "logs": job.get("logs", []),
            "result": job.get("result"),
            "error": job.get("error")
        }

    # 否则返回数据库状态
    return {
        "model_id": model_id,
        "status": db_status,
        "metrics": metrics,
        "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else None
    }


@router.delete('/{model_id}')
def delete_model(model_id: int, current_user: dict = Depends(get_current_user)):
    """删除模型"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # 获取模型文件路径
        cur.execute("SELECT file_path FROM t_model WHERE id = %s", (model_id,))
        row = cur.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": "模型不存在"})
        
        file_path = row[0]
        
        # 删除文件：先删 MinIO，再删本地
        if file_path:
            # MinIO 删除
            try:
                from backend.storage import get_storage
                get_storage().delete(file_path)
            except Exception as e:
                print(f"[delete_model] MinIO 删除失败（忽略）: {e}")
            # 本地文件删除
            full_path = os.path.join(ROOT_DIR, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        # 删除数据库记录
        cur.execute("DELETE FROM t_model WHERE id = %s", (model_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "模型已删除", "model_id": model_id}
        
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})

