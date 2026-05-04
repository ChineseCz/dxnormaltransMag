"""api/ml/predict.py  ──  物理场预测接口"""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Any, Optional
import os, time, random, json, tempfile, shutil, math
import numpy as np

router = APIRouter()

_HERE        = os.path.dirname(os.path.abspath(__file__))    # api/ml/
_BACKEND_DIR = os.path.dirname(os.path.dirname(_HERE))        # backend/
ROOT_DIR     = os.path.dirname(_BACKEND_DIR)                  # project root

DATASETS_DIR = os.path.join(_BACKEND_DIR, 'datasets')

# ─── 旧的仿真数据接口（保留，供设备可视化用）───────────────────────
CORE_DIR     = os.path.join(ROOT_DIR, 'core_algorithms')
SPLIT_OUTPUT_DIR = os.path.join(CORE_DIR, 'data', 'splited data', 'output')
TEST_OUTPUT_DIR  = os.path.join(CORE_DIR, 'data', 'test data',   'output')
COORD_FILE       = os.path.join(CORE_DIR, 'data', 'zuobiao.txt')
PRED_FILE        = os.path.join(CORE_DIR, 'result', 'DNN', 'predY_DNNmodel_rebuild.txt')

_coords_cache = None
_pred_cache   = None
_test_timesteps_cache = None


def _safe_float(v, default=0.0):
    """将 nan/inf 替换为合法 JSON 数值"""
    try:
        f = float(v)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return default


def _sanitize_list(lst):
    """递归清洗列表中的 nan/inf"""
    return [_safe_float(v) for v in lst]


def _sanitize_coords(coords_list):
    """清洗坐标字典列表"""
    result = []
    for c in coords_list:
        result.append({k: _safe_float(v) for k, v in c.items()})
    return result


def _load_coords():
    global _coords_cache
    if _coords_cache is None:
        _coords_cache = np.loadtxt(COORD_FILE)
    return _coords_cache


def _load_predictions():
    global _pred_cache, _test_timesteps_cache
    if _pred_cache is None:
        _pred_cache = np.loadtxt(PRED_FILE)
        _test_timesteps_cache = sorted(
            f.replace('.txt', '') for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.txt')
        )
    return _pred_cache, _test_timesteps_cache


@router.get('/timesteps')
def list_timesteps():
    if not os.path.isdir(SPLIT_OUTPUT_DIR):
        return {'timesteps': [], 'testTimesteps': [], 'total': 0, 'testCount': 0,
                'warning': '旧版数据目录不存在，此接口仅供变压器历史数据使用'}
    all_ts  = sorted(f.replace('.txt','') for f in os.listdir(SPLIT_OUTPUT_DIR) if f.endswith('.txt'))
    test_ts = sorted(f.replace('.txt','') for f in os.listdir(TEST_OUTPUT_DIR)  if f.endswith('.txt')) \
              if os.path.isdir(TEST_OUTPUT_DIR) else []
    return {'timesteps': all_ts, 'testTimesteps': test_ts,
            'total': len(all_ts), 'testCount': len(test_ts)}


@router.get('/field3d')
def get_field3d(
    t:      str = Query(..., description="时间步，如 '0.0400'"),
    source: str = Query('real', description="'real' | 'predicted'"),
):
    if not os.path.isfile(COORD_FILE):
        return JSONResponse(status_code=404, content={
            'error': '旧版坐标文件不存在，此接口仅供变压器历史数据可视化使用',
            'file': COORD_FILE,
        })
    try:
        coords = _load_coords()
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': f'坐标文件读取失败: {e}'})

    if source == 'predicted':
        if not os.path.isfile(PRED_FILE):
            return JSONResponse(status_code=404, content={'error': f'预测结果文件不存在: {PRED_FILE}'})
        try:
            pred_matrix, test_ts = _load_predictions()
        except Exception as e:
            return JSONResponse(status_code=500, content={'error': f'预测文件读取失败: {e}'})
        if t not in test_ts:
            return JSONResponse(status_code=404, content={
                'error': f'时间步 {t}s 不在测试集中', 'available': test_ts})
        values = pred_matrix[test_ts.index(t)]
    else:
        fpath = os.path.join(SPLIT_OUTPUT_DIR, f'{t}.txt')
        if not os.path.isfile(fpath):
            return JSONResponse(status_code=404, content={'error': f'时间步 {t}s 不存在'})
        values = np.loadtxt(fpath)[:, 3]

    v_min, v_max = float(np.min(values)), float(np.max(values))
    points = [{'x': round(float(coords[i,0]),4), 'y': round(float(coords[i,1]),4),
               'z': round(float(coords[i,2]),4), 'value': round(float(values[i]),8)}
              for i in range(len(values))]
    return {'points': points, 'timestep': t, 'source': source,
            'nPoints': len(points), 'vMin': v_min, 'vMax': v_max}


# ─── 真实推理接口 ──────────────────────────────────────────────────

class RealtimeRequest(BaseModel):
    model_id:    int               # t_model.id
    input_array: List[float]       # 原始输入（未归一化）
    dataset_id:  Optional[str] = None   # 可选，用于校验


def _get_model_record(model_id: int):
    """从 DB 查模型记录，返回 dict 或 None"""
    try:
        from backend.db_pg import get_conn
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, dataset_id, model_type, file_path, config, metrics, status "
            "FROM t_model WHERE id=%s",
            (model_id,)
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        if row is None:
            return None
        cols = ['id','dataset_id','model_type','file_path','config','metrics','status']
        d = dict(zip(cols, row))
        # config / metrics 可能是 dict 或 json string
        for k in ('config','metrics'):
            if isinstance(d[k], str):
                try: d[k] = json.loads(d[k])
                except: d[k] = {}
            elif d[k] is None:
                d[k] = {}
        return d
    except Exception as e:
        raise RuntimeError(f"查询模型记录失败: {e}")


def _pull_file(storage, remote_path: str, local_path: str, fallback_local: str = None) -> bool:
    """从 storage 拉文件到 local_path；失败时尝试 fallback_local 本地复制"""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        storage.load_file(remote_path, local_path)
        return True
    except Exception:
        pass
    if fallback_local and os.path.exists(fallback_local):
        shutil.copy2(fallback_local, local_path)
        return True
    return False


def _parse_hidden_layers(raw) -> list:
    """将前端格式 [{id,units,activation}, ...] 或 [16,32,64] 统一转为 [int, ...]"""
    if not raw:
        return None
    result = []
    for h in raw:
        if isinstance(h, dict):
            result.append(int(h.get('units', 64)))
        else:
            result.append(int(h))
    return result if result else None


def _parse_conv_layers(raw) -> list:
    """将前端格式 [{id,filters,kernelSize,pooling,...}, ...] 转为 train_utils 期待的格式"""
    if not raw:
        return None
    result = []
    for c in raw:
        if isinstance(c, dict):
            result.append({
                'filters':     int(c.get('filters', 32)),
                'kernel_size': int(c.get('kernelSize') or c.get('kernel_size', 3)),
                'pooling':     bool(c.get('pooling', False)),
            })
        else:
            result.append(c)
    return result if result else None


def _load_torch_model(model_type: str, model_path: str, input_dim: int, output_dim: int,
                      config: dict):
    """加载 DNN / CNN PyTorch 模型"""
    import torch
    from .train_utils import DNNModel, CNN1DModel

    mtype = model_type.upper()
    if mtype == 'CNN':
        conv_layers = _parse_conv_layers(config.get('conv_layers'))
        fc_units    = int(config.get('fc_units', 256))
        net = CNN1DModel(input_dim, output_dim, conv_layers=conv_layers, fc_units=fc_units)
    else:
        hidden_layers = _parse_hidden_layers(config.get('hidden_layers'))
        net = DNNModel(input_dim, output_dim, hidden_layers=hidden_layers)

    state = torch.load(model_path, map_location='cpu', weights_only=True)
    net.load_state_dict(state)
    net.eval()
    return net


@router.post('/realtime')
def realtime_predict(body: RealtimeRequest):
    t0 = time.time()

    # 1. 查 DB 获取模型信息
    try:
        model_rec = _get_model_record(body.model_id)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

    if model_rec is None:
        return JSONResponse(status_code=404, content={'error': f'模型 {body.model_id} 不存在'})
    if model_rec['status'] != 'done':
        return JSONResponse(status_code=400, content={'error': '模型尚未训练完成'})

    dataset_id  = model_rec['dataset_id']
    model_type  = model_rec['model_type']
    file_path   = model_rec['file_path']       # MinIO path 或本地相对路径
    config      = model_rec['config'] or {}
    metrics     = model_rec['metrics'] or {}

    input_dim   = int(metrics.get('input_dim',  len(body.input_array)))
    output_dim  = int(metrics.get('output_dim', 60))
    used_pca    = bool(metrics.get('used_pca',   False))
    used_zscore = bool(metrics.get('used_zscore', False))

    # 验证输入维度
    if len(body.input_array) != input_dim:
        return JSONResponse(status_code=400, content={
            'error': f'输入维度不匹配：模型需要 {input_dim} 个输入，收到 {len(body.input_array)} 个'
        })

    # 2. 准备临时目录
    tmp_root = tempfile.mkdtemp(prefix=f'infer_{body.model_id}_')
    tmp_model = os.path.join(tmp_root, 'model')
    tmp_data  = os.path.join(tmp_root, 'data')
    tmp_pca   = os.path.join(tmp_root, 'pca_result')
    os.makedirs(tmp_model, exist_ok=True)
    os.makedirs(tmp_data,  exist_ok=True)
    os.makedirs(tmp_pca,   exist_ok=True)

    dataset_dir = os.path.join(DATASETS_DIR, dataset_id)
    data_dir    = os.path.join(dataset_dir, 'data')
    pca_dir_local = os.path.join(dataset_dir, 'pca_result')

    try:
        # 3. 初始化 storage
        try:
            from backend.storage import get_storage
            storage = get_storage()
            use_storage = True
        except Exception:
            use_storage = False

        # 4. 拉模型文件
        model_filename = os.path.basename(file_path) if file_path else ''
        local_model_path = os.path.join(tmp_model, model_filename)

        pulled_model = False
        if use_storage and file_path:
            pulled_model = _pull_file(
                storage, file_path, local_model_path,
                os.path.join(dataset_dir, 'model', model_filename)
            )
        if not pulled_model:
            # 直接用本地路径
            candidates = [
                os.path.join(dataset_dir, 'model', model_filename),
                os.path.join(_BACKEND_DIR, file_path.lstrip('/')) if file_path else '',
            ]
            for c in candidates:
                if c and os.path.exists(c):
                    shutil.copy2(c, local_model_path)
                    pulled_model = True
                    break

        if not pulled_model:
            return JSONResponse(status_code=404, content={'error': f'模型文件未找到: {file_path}'})

        # 5. 归一化输入
        x = np.array(body.input_array, dtype=np.float32)

        if used_zscore:
            mu_path    = os.path.join(tmp_data, 'zstrainmuInput.txt')
            sigma_path = os.path.join(tmp_data, 'zstrainsigmaInput.txt')
            if use_storage:
                _pull_file(storage, f'datasets/{dataset_id}/data/zstrainmuInput.txt',    mu_path,    os.path.join(data_dir, 'zstrainmuInput.txt'))
                _pull_file(storage, f'datasets/{dataset_id}/data/zstrainsigmaInput.txt', sigma_path, os.path.join(data_dir, 'zstrainsigmaInput.txt'))
            else:
                for src, dst in [(os.path.join(data_dir,'zstrainmuInput.txt'), mu_path),
                                  (os.path.join(data_dir,'zstrainsigmaInput.txt'), sigma_path)]:
                    if os.path.exists(src): shutil.copy2(src, dst)

            if os.path.exists(mu_path) and os.path.exists(sigma_path):
                mu    = np.loadtxt(mu_path).astype(np.float32)
                sigma = np.loadtxt(sigma_path).astype(np.float32)
                sigma = np.where(sigma < 1e-10, 1.0, sigma)
                x = (x - mu) / sigma

        # 6. 推理
        x_in = x.reshape(1, -1)   # (1, input_dim)

        if model_type.upper() in ('DNN', 'CNN'):
            import torch
            net = _load_torch_model(model_type, local_model_path, input_dim, output_dim, config)
            with torch.no_grad():
                y_pred = net(torch.FloatTensor(x_in)).numpy()[0]   # (output_dim,)
        elif model_type.upper() == 'RF':
            import joblib
            rf = joblib.load(local_model_path)
            y_pred = rf.predict(x_in)[0]   # (output_dim,) or scalar
            if np.isscalar(y_pred): y_pred = np.array([y_pred])
        else:
            return JSONResponse(status_code=400, content={'error': f'不支持的模型类型: {model_type}'})

        # 7. 逆 PCA
        field_values = y_pred.copy()
        if used_pca:
            mean_path = os.path.join(tmp_pca, 'mean_pca.txt')
            vec_path  = os.path.join(tmp_pca, 'vector_pca.txt')
            if use_storage:
                _pull_file(storage, f'datasets/{dataset_id}/pca_result/mean_pca.txt',   mean_path,   os.path.join(pca_dir_local,'mean_pca.txt'))
                _pull_file(storage, f'datasets/{dataset_id}/pca_result/vector_pca.txt', vec_path,    os.path.join(pca_dir_local,'vector_pca.txt'))
            else:
                for src, dst in [(os.path.join(pca_dir_local,'mean_pca.txt'), mean_path),
                                  (os.path.join(pca_dir_local,'vector_pca.txt'), vec_path)]:
                    if os.path.exists(src): shutil.copy2(src, dst)

            if os.path.exists(mean_path) and os.path.exists(vec_path):
                pca_mean = np.loadtxt(mean_path).astype(np.float64)   # (raw_dim,)
                pca_vec  = np.loadtxt(vec_path).astype(np.float64)    # (n_comp, raw_dim)
                field_values = (y_pred.astype(np.float64) @ pca_vec + pca_mean).astype(np.float32)

        # 8. 加载坐标（优先 MinIO，fallback 本地）
        tmp_coord = os.path.join(tmp_data, 'coordinates.txt')
        coord_local = os.path.join(data_dir, 'coordinates.txt')
        if use_storage:
            _pull_file(storage, f'datasets/{dataset_id}/data/coordinates.txt',
                       tmp_coord, coord_local)
        else:
            if os.path.exists(coord_local):
                shutil.copy2(coord_local, tmp_coord)

        coordinates = []
        if os.path.exists(tmp_coord):
            coords = np.loadtxt(tmp_coord)
            if coords.ndim == 1:
                coords = coords.reshape(-1, 1)
            n_cols = coords.shape[1] if coords.ndim > 1 else 1
            if n_cols >= 3:
                # 3D: x, y, z
                coordinates = [
                    {'x': float(coords[i, 0]), 'y': float(coords[i, 1]), 'z': float(coords[i, 2])}
                    for i in range(len(coords))
                ]
            elif n_cols == 2:
                # 2D 轴对称 (r, z)：绕 z 轴旋转展开为 3D 旋转体，同步复制场值
                N_ANGLES = 6    # 每个截面点展开 6 个角度（60° 间隔）
                MAX_BASE = 3000 # 截面点上限，超过则均匀采样（控制返回总点数 ≤ 18000）
                angles = np.linspace(0, 2 * np.pi, N_ANGLES, endpoint=False)
                base_idx = np.arange(len(coords))
                if len(base_idx) > MAX_BASE:
                    rng = np.random.default_rng(42)
                    base_idx = rng.choice(base_idx, MAX_BASE, replace=False)
                expanded_coords = []
                expanded_values = []
                for idx in base_idx:
                    r_val  = float(coords[idx, 0])
                    z_val  = float(coords[idx, 1])
                    fv_val = float(field_values[idx]) if idx < len(field_values) else 0.0
                    for theta in angles:
                        expanded_coords.append({
                            'x': round(r_val * float(np.cos(theta)), 4),
                            'y': round(r_val * float(np.sin(theta)), 4),
                            'z': round(z_val, 4),
                        })
                        expanded_values.append(fv_val)
                coordinates  = expanded_coords
                field_values = np.array(expanded_values, dtype=np.float32)
            else:
                coordinates = [
                    {'x': float(coords[i, 0]), 'y': 0.0, 'z': 0.0}
                    for i in range(len(coords))
                ]

        # 9. 统计
        fv = _sanitize_list(field_values.tolist())
        stats = {
            'min':  _safe_float(np.min(field_values)),
            'max':  _safe_float(np.max(field_values)),
            'mean': _safe_float(np.mean(field_values)),
            'std':  _safe_float(np.std(field_values)),
            'n':    len(fv),
        }
        coordinates = _sanitize_coords(coordinates)

        elapsed = round(time.time() - t0, 3)

        # 10. 持久化预测记录到 t_prediction
        pred_id = None
        try:
            from backend.db_pg import get_conn as _get_conn
            _conn = _get_conn()
            _cur  = _conn.cursor()
            _cur.execute("""
                INSERT INTO t_prediction (dataset_id, model_id, inputs, stats)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (dataset_id, body.model_id,
                  json.dumps(body.input_array),
                  json.dumps(stats)))
            pred_id = _cur.fetchone()[0]
            _conn.commit()
            _cur.close(); _conn.close()
        except Exception as _e:
            print(f"[predict] 持久化预测记录失败（非致命）: {_e}")

        result_dict = {
            'status':        'success',
            'fieldValues':   fv,
            'coordinates':   coordinates,
            'stats':         stats,
            'model_id':      body.model_id,
            'model_type':    model_type,
            'dataset_id':    dataset_id,
            'prediction_id': pred_id,
            'used_pca':      used_pca,
            'used_zscore':   used_zscore,
            'latency_s':     elapsed,
            'msg':           f'推理完成，{len(fv)} 个场点，耗时 {elapsed}s',
        }
        # 用 allow_nan=False 序列化，若仍有残留 nan 则替换为 null
        try:
            safe_body = json.dumps(result_dict, allow_nan=False)
        except ValueError:
            safe_body = json.dumps(result_dict, allow_nan=True).replace('NaN', 'null').replace('Infinity', 'null').replace('-Infinity', 'null')
        return JSONResponse(content=json.loads(safe_body))

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


# ─── 预测历史查询 ──────────────────────────────────────────────────

@router.get('/history')
def list_predictions(
    model_id:   Optional[int] = Query(None),
    dataset_id: Optional[str] = Query(None),
    page:       int           = Query(1, ge=1),
    size:       int           = Query(20, ge=1, le=100),
):
    """查询历史预测记录（分页）"""
    try:
        from backend.db_pg import get_conn as _gc, get_dict_cursor as _gdc
        offset = (page - 1) * size
        where, params = ["1=1"], []
        if model_id is not None:
            where.append("model_id=%s"); params.append(model_id)
        if dataset_id is not None:
            where.append("dataset_id=%s"); params.append(dataset_id)
        wc = " AND ".join(where)

        conn = _gc()
        try:
            with _gdc(conn) as cur:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM t_prediction WHERE {wc}", params)
                total = cur.fetchone()['cnt']
                cur.execute(f"""
                    SELECT id, dataset_id, model_id, inputs, stats, created_at
                    FROM t_prediction WHERE {wc}
                    ORDER BY id DESC LIMIT %s OFFSET %s
                """, params + [size, offset])
                rows = cur.fetchall()
        finally:
            conn.close()

        items = [{
            'id':         r['id'],
            'dataset_id': r['dataset_id'],
            'model_id':   r['model_id'],
            'inputs':     r['inputs'],
            'stats':      r['stats'],
            'created_at': r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r['created_at'] else '',
        } for r in rows]
        return {'total': total, 'list': items}
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={'error': str(e), 'trace': traceback.format_exc()})

