"""api/devices/gaoya.py  ──  高压套管 Po_r 物理场可视化接口"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import os, re
import numpy as np

router = APIRouter()

_HERE    = os.path.dirname(os.path.abspath(__file__))   # api/devices/
_BACKEND = os.path.dirname(os.path.dirname(_HERE))       # backend/
ROOT_DIR = os.path.dirname(_BACKEND)                     # project root

DATA_DIR = os.path.join(ROOT_DIR, 'core_algorithms', '高压套管', 'B-RowData', '60HzPo_r_output100_5000A')


def _current_files():
    result = {}
    if not os.path.isdir(DATA_DIR):
        return result
    for fname in os.listdir(DATA_DIR):
        m = re.match(r'Po_r_output(\d+)A\.txt$', fname)
        if m:
            result[int(m.group(1))] = fname
    return result


CURRENT_FILES   = _current_files()
AVAILABLE       = sorted(CURRENT_FILES)
_cache: dict    = {}
_HEADER_LINES   = 9
_MAX_RENDER_PTS = 8000


def _load_data(current: int) -> np.ndarray:
    if current in _cache:
        return _cache[current]
    fname = CURRENT_FILES.get(current)
    if fname is None:
        raise FileNotFoundError(f'找不到 {current}A 对应的数据文件')
    raw = np.loadtxt(os.path.join(DATA_DIR, fname), skiprows=_HEADER_LINES)
    _cache[current] = raw
    return raw


def _sample_points(data: np.ndarray, n: int = _MAX_RENDER_PTS) -> list:
    po_r = data[:, 3]
    nonzero_mask = po_r > 1e-6
    idx_nz = np.where(nonzero_mask)[0]
    idx_z  = np.where(~nonzero_mask)[0]
    n_nz = min(len(idx_nz), int(n * 0.75))
    n_z  = min(len(idx_z),  n - n_nz)
    rng  = np.random.default_rng(42)
    sel_nz = rng.choice(idx_nz, size=n_nz, replace=False) if n_nz > 0 else np.array([], dtype=int)
    sel_z  = rng.choice(idx_z,  size=n_z,  replace=False) if n_z  > 0 else np.array([], dtype=int)
    sel = np.concatenate([sel_nz, sel_z])
    rng.shuffle(sel)
    pts = data[sel]
    return [{'x': round(float(pts[i,0]),4), 'y': round(float(pts[i,1]),4),
              'z': round(float(pts[i,2]),4), 'value': round(float(pts[i,3]),6)}
            for i in range(len(pts))]


@router.get('/currents')
def list_currents():
    return {'currents': AVAILABLE, 'count': len(AVAILABLE), 'unit': 'A', 'step': 100,
            'min': AVAILABLE[0] if AVAILABLE else None, 'max': AVAILABLE[-1] if AVAILABLE else None}


@router.get('/field3d')
def get_field3d(
    current: int = Query(1000, description="电流档位 (A)"),
    n:       int = Query(_MAX_RENDER_PTS, description="最大返回散点数"),
):
    n_pts = max(100, min(n, 20000))
    if current not in CURRENT_FILES:
        return JSONResponse(status_code=404, content={
            'error': f'{current}A 不在可用档位中', 'available': AVAILABLE})
    try:
        data = _load_data(current)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    po_r = data[:, 3]
    return {'points': _sample_points(data, n=n_pts), 'current': current,
            'nTotal': len(data), 'nSampled': n_pts,
            'nonZeroCount': int(np.sum(po_r > 1e-6)),
            'vMin': float(np.min(po_r)), 'vMax': float(np.max(po_r)),
            'unit': 'W/m³', 'label': 'Po_r',
            'description': f'高压套管功率损耗密度场 @ {current} A (60 Hz)'}


@router.get('/stats')
def get_stats(current: int = Query(1000)):
    if current not in CURRENT_FILES:
        return JSONResponse(status_code=404, content={'error': f'{current}A 不在可用档位'})
    try:
        data = _load_data(current)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    po_r = data[:, 3]
    nz   = po_r[po_r > 1e-6]
    return {'current': current, 'nTotal': int(len(data)), 'nonZeroCount': int(len(nz)),
            'poMin': float(np.min(po_r)), 'poMax': float(np.max(po_r)),
            'poMean': float(np.mean(nz)) if len(nz) else 0.0,
            'poP95':  float(np.percentile(nz, 95)) if len(nz) else 0.0,
            'xRange': [float(data[:,0].min()), float(data[:,0].max())],
            'yRange': [float(data[:,1].min()), float(data[:,1].max())],
            'zRange': [float(data[:,2].min()), float(data[:,2].max())],
            'unit': 'W/m³'}

