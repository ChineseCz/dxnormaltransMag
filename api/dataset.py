"""
数据集管理 API —— 支持多设备、多物理场的通用数据集管理
每个数据集拥有独立的目录结构：
  datasets/<id>/raw/         原始上传文件
  datasets/<id>/data/        处理后的数据文件
  datasets/<id>/pca_result/  PCA 结果
  datasets/<id>/model/       模型文件
  datasets/<id>/result/      预测结果
"""

from flask import Blueprint, request, jsonify
import os, json, uuid, shutil
from datetime import datetime
import numpy as np

dataset_bp = Blueprint('dataset', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, 'datasets')
DATASETS_META = os.path.join(DATASETS_DIR, 'datasets.json')
os.makedirs(DATASETS_DIR, exist_ok=True)

# ───────────── 预定义的设备类型与物理场类型 ─────────────

DEVICE_TYPES = [
    {"value": "transformer",  "label": "变压器",  "icon": "⚡"},
    {"value": "reactor",      "label": "电抗器",  "icon": "🔌"},
    {"value": "motor",        "label": "电机",    "icon": "⚙️"},
    {"value": "gis",          "label": "GIS",     "icon": "🏗️"},
    {"value": "cable",        "label": "电缆",    "icon": "🔗"},
    {"value": "busbar",       "label": "母线",    "icon": "📏"},
    {"value": "other",        "label": "其他",    "icon": "📦"},
]

FIELD_TYPES = [
    {"value": "magnetic",     "label": "磁场",   "unit": "T",    "unitLabel": "磁通密度 B"},
    {"value": "temperature",  "label": "温度场", "unit": "°C",   "unitLabel": "温度 T"},
    {"value": "stress",       "label": "应力场", "unit": "Pa",   "unitLabel": "应力 σ"},
    {"value": "electric",     "label": "电场",   "unit": "V/m",  "unitLabel": "电场强度 E"},
    {"value": "flow",         "label": "流场",   "unit": "m/s",  "unitLabel": "流速 v"},
    {"value": "other",        "label": "其他",   "unit": "",     "unitLabel": "自定义"},
]

# ───────────── JSON 持久化工具 ─────────────

def _load_all():
    if not os.path.exists(DATASETS_META):
        return []
    with open(DATASETS_META, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_all(datasets):
    with open(DATASETS_META, 'w', encoding='utf-8') as f:
        json.dump(datasets, f, ensure_ascii=False, indent=2)

def _find(ds_id):
    for ds in _load_all():
        if ds['id'] == ds_id:
            return ds
    return None

def _update(ds_id, patch: dict):
    datasets = _load_all()
    for i, ds in enumerate(datasets):
        if ds['id'] == ds_id:
            datasets[i].update(patch)
            datasets[i]['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            _save_all(datasets)
            return datasets[i]
    return None

def _ds_dir(ds_id):
    return os.path.join(DATASETS_DIR, ds_id)

# ───────────── 元数据接口 ─────────────

@dataset_bp.route('/types', methods=['GET'])
def get_types():
    return jsonify({"deviceTypes": DEVICE_TYPES, "fieldTypes": FIELD_TYPES})


@dataset_bp.route('/list', methods=['GET'])
def list_datasets():
    return jsonify({"datasets": _load_all()})


@dataset_bp.route('/create', methods=['POST'])
def create_dataset():
    d = request.json
    ds_id = 'ds_' + uuid.uuid4().hex[:8]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    dataset = {
        'id': ds_id,
        'name': d.get('name', '未命名数据集'),
        'deviceType': d.get('deviceType', 'other'),
        'fieldType': d.get('fieldType', 'other'),
        'description': d.get('description', ''),
        'createdAt': now,
        'updatedAt': now,
        # 输入变量列表  [{name, unit}]
        'inputVariables': d.get('inputVariables', []),
        # 输出变量描述  {name, unit, spatialPoints}
        'outputVariable': d.get('outputVariable', {}),
        'timeStep': d.get('timeStep', 0.0005),
        'coordCols': d.get('coordCols', 3),
        'files': [],
        'processConfig': {
            't0': d.get('t0', 0.04),
            'tEnd': d.get('tEnd', 0.1),
            'dt': d.get('timeStep', 0.0005),
            'splitRatio': 0.8,
            'pcaComponents': 60,
        },
        'pipelineStatus': {'cut': False, 'split': False, 'zscore': False, 'pca': False},
        'trainInfo': None,
    }

    for sub in ('raw', 'data', 'pca_result', 'model', 'result'):
        os.makedirs(os.path.join(_ds_dir(ds_id), sub), exist_ok=True)

    all_ds = _load_all()
    all_ds.append(dataset)
    _save_all(all_ds)
    return jsonify({"message": "数据集创建成功", "dataset": dataset})


@dataset_bp.route('/<ds_id>', methods=['GET'])
def get_dataset(ds_id):
    ds = _find(ds_id)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404
    return jsonify({"dataset": ds})


@dataset_bp.route('/<ds_id>', methods=['PUT'])
def update_dataset_api(ds_id):
    ds = _update(ds_id, request.json)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404
    return jsonify({"message": "更新成功", "dataset": ds})


@dataset_bp.route('/<ds_id>', methods=['DELETE'])
def delete_dataset(ds_id):
    datasets = _load_all()
    new_list = [d for d in datasets if d['id'] != ds_id]
    if len(new_list) == len(datasets):
        return jsonify({"error": "数据集不存在"}), 404
    d = os.path.join(DATASETS_DIR, ds_id)
    if os.path.exists(d):
        shutil.rmtree(d)
    _save_all(new_list)
    return jsonify({"message": "数据集已删除"})

# ───────────── 文件管理 ─────────────

@dataset_bp.route('/<ds_id>/upload', methods=['POST'])
def upload_to_dataset(ds_id):
    ds = _find(ds_id)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404
    if 'file' not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    f = request.files['file']
    role = request.form.get('role', 'unknown')            # input / output / coordinate
    var_idx = request.form.get('variableIndex', None)

    raw_dir = os.path.join(_ds_dir(ds_id), 'raw')
    fpath = os.path.join(raw_dir, f.filename)
    f.save(fpath)

    # 基本维度分析
    analysis = {'rows': 0, 'cols': 0}
    try:
        arr = np.loadtxt(fpath, encoding='utf-8', comments='%')
        analysis = {'rows': int(arr.shape[0]),
                     'cols': int(arr.shape[1]) if arr.ndim > 1 else 1}
    except Exception:
        pass

    file_info = {
        'filename': f.filename,
        'role': role,
        'variableIndex': int(var_idx) if var_idx is not None else None,
        'size': os.path.getsize(fpath),
        'analysis': analysis,
        'uploadTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    datasets = _load_all()
    for d in datasets:
        if d['id'] == ds_id:
            d['files'] = [x for x in d['files'] if x['filename'] != f.filename]
            d['files'].append(file_info)
            if role == 'output' and analysis['rows'] > 0:
                d['outputVariable']['spatialPoints'] = analysis['rows']
            break
    _save_all(datasets)
    return jsonify({"message": f"{f.filename} 上传成功", "file": file_info, "analysis": analysis})


@dataset_bp.route('/<ds_id>/files/<filename>', methods=['DELETE'])
def delete_file(ds_id, filename):
    ds = _find(ds_id)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404
    fpath = os.path.join(_ds_dir(ds_id), 'raw', filename)
    if os.path.exists(fpath):
        os.remove(fpath)
    datasets = _load_all()
    for d in datasets:
        if d['id'] == ds_id:
            d['files'] = [x for x in d['files'] if x['filename'] != filename]
            break
    _save_all(datasets)
    return jsonify({"message": f"{filename} 已删除"})


@dataset_bp.route('/<ds_id>/files/<filename>/role', methods=['PUT'])
def update_file_role(ds_id, filename):
    """修改已上传文件的角色"""
    body = request.json
    datasets = _load_all()
    for d in datasets:
        if d['id'] == ds_id:
            for fobj in d['files']:
                if fobj['filename'] == filename:
                    fobj['role'] = body.get('role', fobj['role'])
                    fobj['variableIndex'] = body.get('variableIndex', fobj.get('variableIndex'))
                    break
            break
    _save_all(datasets)
    return jsonify({"message": "角色已更新"})

# ───────────── 数据处理流水线 ─────────────

@dataset_bp.route('/<ds_id>/process', methods=['POST'])
def process_dataset(ds_id):
    ds = _find(ds_id)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404

    body = request.json
    step = body.get('step')
    params = body.get('params', {})

    raw_dir = os.path.join(_ds_dir(ds_id), 'raw')
    data_dir = os.path.join(_ds_dir(ds_id), 'data')
    pca_dir = os.path.join(_ds_dir(ds_id), 'pca_result')
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(pca_dir, exist_ok=True)

    try:
        if step == 'cut':
            return _step_cut(ds, raw_dir, data_dir, params)
        elif step == 'split':
            return _step_split(ds, data_dir, params)
        elif step == 'normalize':
            return _step_normalize(ds, data_dir, params)
        elif step == 'pca':
            return _step_pca(ds, data_dir, pca_dir, params)
        else:
            return jsonify({"error": f"未知步骤: {step}"}), 400
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


def _step_cut(ds, raw_dir, data_dir, params):
    """Step 1: 截取稳态时间窗口"""
    t0   = float(params.get('t0', ds['processConfig']['t0']))
    tEnd = float(params.get('tEnd', ds['processConfig'].get('tEnd', 0.1)))
    dt   = float(params.get('dt', ds['processConfig']['dt']))
    coord_cols = int(ds.get('coordCols', 3))

    # ---- 输出文件 ----
    output_files = [f for f in ds.get('files', []) if f['role'] == 'output']
    if not output_files:
        return jsonify({"error": "未找到角色为「输出」的数据文件"}), 400
    out_data = np.loadtxt(os.path.join(raw_dir, output_files[0]['filename']),
                          encoding='utf-8', comments='%')
    # out_data: (spatial_points, coord_cols + time_steps)
    n_total_time = out_data.shape[1] - coord_cols
    start_idx = int(round(t0 / dt))
    end_idx = min(int(round(tEnd / dt)), n_total_time)
    n_cut = end_idx - start_idx

    coords = out_data[:, :coord_cols]
    cut_output = out_data[:, (coord_cols + start_idx):(coord_cols + end_idx)]
    np.savetxt(os.path.join(data_dir, 'coordinates.txt'), coords)
    np.savetxt(os.path.join(data_dir, 'cutOutput.txt'), cut_output)

    # ---- 输入文件（按 variableIndex 排序拼接）----
    input_files = sorted(
        [f for f in ds.get('files', []) if f['role'] == 'input'],
        key=lambda x: x.get('variableIndex', 0) or 0
    )
    input_arrays = []
    for fobj in input_files:
        arr = np.loadtxt(os.path.join(raw_dir, fobj['filename']),
                         encoding='utf-8', comments='%')
        vals = arr[:, 1] if arr.ndim > 1 and arr.shape[1] >= 2 else arr
        input_arrays.append(vals[start_idx:end_idx])

    cut_input = np.column_stack(input_arrays) if input_arrays else np.zeros((n_cut, 1))
    np.savetxt(os.path.join(data_dir, 'cutInput.txt'), cut_input)

    # 更新元数据
    _update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'cut': True},
        'processConfig': {**ds['processConfig'], 't0': t0, 'tEnd': tEnd, 'dt': dt},
    })
    return jsonify({
        "status": "success",
        "msg": f"截取完成：{n_cut} 个时间步 × {cut_output.shape[0]} 个空间点，输入 {cut_input.shape[1]} 维"
    })


def _step_split(ds, data_dir, params):
    """Step 2: 训练/测试集划分"""
    ratio = float(params.get('splitRatio', ds['processConfig']['splitRatio']))
    cut_input  = np.loadtxt(os.path.join(data_dir, 'cutInput.txt'))
    cut_output = np.loadtxt(os.path.join(data_dir, 'cutOutput.txt'))

    # cutOutput: (spatial_points, n_time_steps) → 转置为 (n_time_steps, spatial_points)
    if cut_output.shape[0] > cut_output.shape[1]:
        cut_output = cut_output.T

    n = cut_input.shape[0]
    n_train = int(n * ratio)
    idx = np.random.permutation(n)
    tr, te = idx[:n_train], idx[n_train:]

    np.savetxt(os.path.join(data_dir, 'trainInput.txt'),  cut_input[tr])
    np.savetxt(os.path.join(data_dir, 'testInput.txt'),   cut_input[te])
    np.savetxt(os.path.join(data_dir, 'trainOutput.txt'), cut_output[tr])
    np.savetxt(os.path.join(data_dir, 'testOutput.txt'),  cut_output[te])

    _update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'split': True},
        'processConfig': {**ds['processConfig'], 'splitRatio': ratio},
    })
    return jsonify({
        "status": "success",
        "msg": f"划分完成：训练集 {n_train} 条，测试集 {n - n_train} 条"
    })


def _step_normalize(ds, data_dir, params):
    """Step 3: Z-Score 标准化（仅对输入）"""
    trX = np.loadtxt(os.path.join(data_dir, 'trainInput.txt'))
    teX = np.loadtxt(os.path.join(data_dir, 'testInput.txt'))
    if trX.ndim == 1:
        trX, teX = trX.reshape(-1, 1), teX.reshape(-1, 1)

    mu = np.mean(trX, axis=0, keepdims=True)
    sigma = np.std(trX, axis=0, keepdims=True)
    sigma[sigma == 0] = 1.0

    np.savetxt(os.path.join(data_dir, 'zstrainInput.txt'), (trX - mu) / sigma)
    np.savetxt(os.path.join(data_dir, 'zstestInput.txt'),  (teX - mu) / sigma)
    np.savetxt(os.path.join(data_dir, 'zstrainmuInput.txt'), mu)
    np.savetxt(os.path.join(data_dir, 'zstrainsigmaInput.txt'), sigma)

    _update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'zscore': True},
    })
    return jsonify({"status": "success", "msg": f"归一化完成：输入 {trX.shape[1]} 维"})


def _step_pca(ds, data_dir, pca_dir, params):
    """Step 4: PCA 降维（对输出场数据）"""
    from sklearn.decomposition import PCA

    n_comp = int(params.get('pcaComponents', ds['processConfig']['pcaComponents']))
    trY = np.loadtxt(os.path.join(data_dir, 'trainOutput.txt'))
    teY = np.loadtxt(os.path.join(data_dir, 'testOutput.txt'))

    actual = min(n_comp, trY.shape[1], trY.shape[0])
    pca = PCA(n_components=actual)
    tr_pca = pca.fit_transform(trY)
    te_pca = np.matmul(teY - pca.mean_, pca.components_.T)

    np.savetxt(os.path.join(data_dir, 'trainPCA.txt'), tr_pca)
    np.savetxt(os.path.join(data_dir, 'testPCA.txt'),  te_pca)
    np.savetxt(os.path.join(pca_dir, 'mean_pca.txt'), pca.mean_)
    np.savetxt(os.path.join(pca_dir, 'vector_pca.txt'), pca.components_)
    np.savetxt(os.path.join(pca_dir, 'variance_pca.txt'), pca.explained_variance_ratio_)

    var_sum = float(pca.explained_variance_ratio_.sum())

    # 计算并保存 trainInfo
    try:
        zsX = np.loadtxt(os.path.join(data_dir, 'zstrainInput.txt'))
        zsXt = np.loadtxt(os.path.join(data_dir, 'zstestInput.txt'))
        in_dim = zsX.shape[1] if zsX.ndim > 1 else 1
        train_info = {
            'trainSamples': int(tr_pca.shape[0]),
            'testSamples': int(te_pca.shape[0]),
            'inputDim': int(in_dim),
            'outputDim': int(actual),
            'rawOutputDim': int(trY.shape[1]),
            'trainRatio': round(tr_pca.shape[0] / (tr_pca.shape[0] + te_pca.shape[0]), 2),
            'varianceExplained': round(var_sum, 4),
        }
        _update(ds['id'], {'trainInfo': train_info})
    except Exception:
        pass

    _update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'pca': True},
        'processConfig': {**ds['processConfig'], 'pcaComponents': actual},
    })
    return jsonify({
        "status": "success",
        "msg": f"PCA 降维完成：{trY.shape[1]} → {actual} 维，累计方差解释率 {var_sum*100:.1f}%"
    })

# ───────────── 状态查询 ─────────────

@dataset_bp.route('/<ds_id>/status', methods=['GET'])
def get_status(ds_id):
    ds = _find(ds_id)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404

    dd = os.path.join(_ds_dir(ds_id), 'data')
    pd = os.path.join(_ds_dir(ds_id), 'pca_result')

    def _exists(*names, base=dd):
        return all(os.path.isfile(os.path.join(base, n)) for n in names)

    pipeline = {
        'cut':    {'done': _exists('cutInput.txt', 'cutOutput.txt')},
        'split':  {'done': _exists('trainInput.txt', 'trainOutput.txt', 'testInput.txt', 'testOutput.txt')},
        'zscore': {'done': _exists('zstrainInput.txt', 'zstestInput.txt')},
        'pca':    {'done': _exists('trainPCA.txt', 'testPCA.txt') and _exists('mean_pca.txt', base=pd)},
    }
    ready = all(v['done'] for v in pipeline.values())

    train_info = ds.get('trainInfo')
    if ready and not train_info:
        try:
            zsX  = np.loadtxt(os.path.join(dd, 'zstrainInput.txt'))
            zsXt = np.loadtxt(os.path.join(dd, 'zstestInput.txt'))
            trP  = np.loadtxt(os.path.join(dd, 'trainPCA.txt'))
            trY  = np.loadtxt(os.path.join(dd, 'trainOutput.txt'))
            train_info = {
                'trainSamples': int(zsX.shape[0]),
                'testSamples': int(zsXt.shape[0]),
                'inputDim': int(zsX.shape[1]) if zsX.ndim > 1 else 1,
                'outputDim': int(trP.shape[1]) if trP.ndim > 1 else 1,
                'rawOutputDim': int(trY.shape[1]) if trY.ndim > 1 else 1,
                'trainRatio': round(zsX.shape[0] / (zsX.shape[0] + zsXt.shape[0]), 2),
            }
            _update(ds_id, {'trainInfo': train_info})
        except Exception:
            pass

    return jsonify({
        'pipeline': pipeline,
        'ready': ready,
        'trainInfo': train_info,
        'processConfig': ds.get('processConfig', {}),
    })


@dataset_bp.route('/<ds_id>/auto-detect', methods=['POST'])
def auto_detect(ds_id):
    """自动检测稳态起始点"""
    ds = _find(ds_id)
    if not ds:
        return jsonify({"error": "数据集不存在"}), 404

    raw_dir = os.path.join(_ds_dir(ds_id), 'raw')
    input_files = [f for f in ds.get('files', []) if f['role'] == 'input']
    if not input_files:
        return jsonify({"error": "未找到输入数据文件"}), 400

    fpath = os.path.join(raw_dir, input_files[0]['filename'])
    data = np.loadtxt(fpath, encoding='utf-8', comments='%')
    signal = data[:, 1] if data.ndim > 1 else data

    dt = float(ds.get('timeStep', 0.0005))
    freq = 50  # 工频
    period_samples = int(round(1.0 / freq / dt))
    n = len(signal)

    # 滑动窗口 RMSE 比较相邻周期
    best_t0, best_score = 0.0, float('inf')
    for start in range(0, n - 2 * period_samples, period_samples // 4):
        c1 = signal[start:start + period_samples]
        c2 = signal[start + period_samples:start + 2 * period_samples]
        if len(c1) != len(c2):
            continue
        rmse = float(np.sqrt(np.mean((c1 - c2) ** 2)))
        if rmse < best_score:
            best_score = rmse
            best_t0 = start * dt

    return jsonify({
        "t0": round(best_t0, 4),
        "suggested_msg": f"检测到稳态起始约 {best_t0:.4f}s (相邻周期 RMSE={best_score:.6f})"
    })

