"""api/devices/transfield.py  ──  252kV 变压器油纸套管电场/电位可视化接口"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import os, io, re
import numpy as np

router = APIRouter()

_HERE     = os.path.dirname(os.path.abspath(__file__))   # api/devices/
_BACKEND  = os.path.dirname(os.path.dirname(_HERE))       # backend/
ROOT_DIR  = os.path.dirname(_BACKEND)                     # project root

FIELD_DIR = os.path.join(ROOT_DIR, 'core_algorithms', '变压器电场', '电场数据')
POT_DIR   = os.path.join(ROOT_DIR, 'core_algorithms', '变压器电场', '电位数据')
SKIP_ROWS = 8


def _scan_dir(directory: str) -> dict:
    result = {}
    if not os.path.isdir(directory):
        return result
    for fname in os.listdir(directory):
        m = re.search(r'(\d+\.?\d*)kV\.txt$', fname)
        if m:
            result[m.group(1)] = fname
    return result


FIELD_FILES = _scan_dir(FIELD_DIR)
POT_FILES   = _scan_dir(POT_DIR)
VOLTAGES    = sorted(FIELD_FILES.keys(), key=lambda v: float(v))
_cache: dict = {}


def _load(kind: str, voltage: str) -> np.ndarray:
    key = (kind, voltage)
    if key in _cache:
        return _cache[key]
    directory = FIELD_DIR if kind == 'field' else POT_DIR
    files     = FIELD_FILES if kind == 'field' else POT_FILES
    fname     = files.get(voltage)
    if fname is None:
        raise FileNotFoundError(f'{kind} 文件 {voltage} kV 不存在')
    with open(os.path.join(directory, fname), 'rb') as f:
        raw = f.read()
    text       = raw.decode('utf-8', errors='replace')
    data_lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith('%')]
    buf        = '\n'.join(data_lines)
    arr        = np.loadtxt(io.StringIO(buf), delimiter=',' if ',' in data_lines[0] else None)
    arr[:, 0]  = np.where(arr[:, 0] < 1e-6, 0.0, arr[:, 0])
    _cache[key] = arr
    return arr


def _sample(data: np.ndarray, n: int = 6000) -> list:
    val  = data[:, 2]
    p70, p5 = float(np.percentile(val, 70)), float(np.percentile(val, 5))
    idx_h = np.where(val >= p70)[0]
    idx_m = np.where((val >= p5) & (val < p70))[0]
    idx_l = np.where(val < p5)[0]
    n_h   = min(len(idx_h), int(n * 0.60))
    n_m   = min(len(idx_m), int(n * 0.30))
    n_l   = min(len(idx_l), n - n_h - n_m)
    rng   = np.random.default_rng(42)
    sel   = np.concatenate([rng.choice(idx_h, n_h, replace=False),
                             rng.choice(idx_m, n_m, replace=False),
                             rng.choice(idx_l, n_l, replace=False)])
    rng.shuffle(sel)
    pts = data[sel]
    return [{'r': round(float(pts[i,0]),4), 'z': round(float(pts[i,1]),4),
              'value': round(float(pts[i,2]),6)} for i in range(len(pts))]


def _sample_3d(data: np.ndarray, n_base: int = 2000, n_angles: int = 12) -> list:
    val  = data[:, 2]
    p50  = float(np.percentile(val, 50))
    idx_h = np.where(val >= p50)[0]
    idx_l = np.where(val < p50)[0]
    n_h   = min(len(idx_h), int(n_base * 0.65))
    n_l   = min(len(idx_l), n_base - n_h)
    rng   = np.random.default_rng(42)
    sel   = np.concatenate([rng.choice(idx_h, n_h, replace=False),
                             rng.choice(idx_l, n_l, replace=False)])
    base  = data[sel]
    angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
    pts = []
    for r, z, v in base:
        for theta in angles:
            pts.append({'x': round(float(r * np.cos(theta)),3), 'y': round(float(r * np.sin(theta)),3),
                        'z': round(float(z),3), 'value': round(float(v),6)})
    return pts


@router.get('/voltages')
def list_voltages():
    return {'voltages': VOLTAGES, 'count': len(VOLTAGES), 'unit': 'kV',
            'min': float(VOLTAGES[0]) if VOLTAGES else None,
            'max': float(VOLTAGES[-1]) if VOLTAGES else None}


@router.get('/field2d')
def get_field2d(
    voltage: str = Query(default='', description="导杆峰值电压"),
    kind:    str = Query(default='field', description="'field' | 'potential'"),
    n:       int = Query(default=6000, ge=200, le=20000),
):
    if not voltage:
        voltage = VOLTAGES[0] if VOLTAGES else ''
    if kind not in ('field', 'potential'):
        return JSONResponse(status_code=400, content={'error': "kind 必须为 'field' 或 'potential'"})
    files = FIELD_FILES if kind == 'field' else POT_FILES
    if voltage not in files:
        return JSONResponse(status_code=404, content={'error': f'电压 {voltage} kV 不存在', 'available': VOLTAGES})
    try:
        data = _load(kind, voltage)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    val   = data[:, 2]
    unit  = 'kV/mm' if kind == 'field' else 'kV'
    return {'points': _sample(data, n), 'nTotal': int(len(data)), 'nSampled': len(_sample(data, n)),
            'vMin': float(val.min()), 'vMax': float(val.max()),
            'rMin': float(data[:,0].min()), 'rMax': float(data[:,0].max()),
            'zMin': float(data[:,1].min()), 'zMax': float(data[:,1].max()),
            'voltage': voltage, 'kind': kind, 'unit': unit,
            'label': 'E' if kind == 'field' else 'V'}


@router.get('/field3d')
def get_field3d(
    voltage:  str = Query(default=''),
    kind:     str = Query(default='field'),
    n_base:   int = Query(default=2000, ge=100, le=5000),
    n_angles: int = Query(default=12, ge=4, le=36),
):
    if not voltage:
        voltage = VOLTAGES[0] if VOLTAGES else ''
    files = FIELD_FILES if kind == 'field' else POT_FILES
    if voltage not in files:
        return JSONResponse(status_code=404, content={'error': f'电压 {voltage} kV 不存在', 'available': VOLTAGES})
    try:
        data = _load(kind, voltage)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    val  = data[:, 2]
    return {'points': _sample_3d(data, n_base, n_angles), 'nTotal': int(len(data)),
            'nSampled': len(_sample_3d(data, n_base, n_angles)),
            'vMin': float(val.min()), 'vMax': float(val.max()),
            'voltage': voltage, 'kind': kind,
            'unit': 'kV/mm' if kind == 'field' else 'kV'}


@router.get('/stats')
def get_stats(
    voltage: str = Query(default=''),
    kind:    str = Query(default='field'),
):
    if not voltage:
        voltage = VOLTAGES[0] if VOLTAGES else ''
    files = FIELD_FILES if kind == 'field' else POT_FILES
    if voltage not in files:
        return JSONResponse(status_code=404, content={'error': f'电压 {voltage} kV 不存在'})
    try:
        data = _load(kind, voltage)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
    val  = data[:, 2]
    unit = 'kV/mm' if kind == 'field' else 'kV'
    return {'voltage': voltage, 'kind': kind, 'nTotal': int(len(data)),
            'vMin': float(val.min()), 'vMax': float(val.max()),
            'vMean': float(val.mean()), 'vP95': float(np.percentile(val, 95)),
            'rRange': [float(data[:,0].min()), float(data[:,0].max())],
            'zRange': [float(data[:,1].min()), float(data[:,1].max())],
            'unit': unit}

