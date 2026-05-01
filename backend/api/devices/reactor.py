"""api/devices/reactor.py  ──  电抗器轴对称磁场可视化接口"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import os, io
import numpy as np

router = APIRouter()

_HERE     = os.path.dirname(os.path.abspath(__file__))   # api/devices/
_BACKEND  = os.path.dirname(os.path.dirname(_HERE))       # backend/
ROOT_DIR  = os.path.dirname(_BACKEND)                     # project root

DATA_FILE = os.path.join(ROOT_DIR, 'core_algorithms', '电抗器', '100[A[.txt')
_cache    = None


def _load_data() -> np.ndarray:
    global _cache
    if _cache is not None:
        return _cache
    with open(DATA_FILE, 'rb') as f:
        raw = f.read()
    text       = raw.decode('utf-8', errors='replace')
    data_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('%')]
    _cache     = np.loadtxt(io.StringIO('\n'.join(data_lines)))
    return _cache


def _sample_2d(data: np.ndarray, n: int = 6000) -> list:
    B = data[:, 2]
    thresh_75 = float(np.percentile(B, 75))
    idx_h = np.where(B >= thresh_75)[0]
    idx_l = np.where(B < thresh_75)[0]
    n_h = min(len(idx_h), int(n * 0.60))
    n_l = min(len(idx_l), n - n_h)
    rng  = np.random.default_rng(42)
    sel  = np.concatenate([rng.choice(idx_h, n_h, replace=False), rng.choice(idx_l, n_l, replace=False)])
    pts  = data[sel]
    return [{'r': round(float(pts[i,0]),4), 'z': round(float(pts[i,1]),4), 'value': round(float(pts[i,2]),8)}
            for i in range(len(pts))]


def _sample_3d(data: np.ndarray, n_base: int = 2500, n_angles: int = 12) -> list:
    B = data[:, 2]
    thresh_60 = float(np.percentile(B, 60))
    idx_h = np.where(B >= thresh_60)[0]
    idx_l = np.where(B < thresh_60)[0]
    n_h   = min(len(idx_h), int(n_base * 0.65))
    n_l   = min(len(idx_l), n_base - n_h)
    rng   = np.random.default_rng(42)
    sel   = np.concatenate([rng.choice(idx_h, n_h, replace=False), rng.choice(idx_l, n_l, replace=False)])
    base  = data[sel]
    angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
    pts = []
    for r, z, B_val in base:
        for theta in angles:
            pts.append({'x': round(float(r * np.cos(theta)),3), 'y': round(float(r * np.sin(theta)),3),
                        'z': round(float(z),3), 'value': round(float(B_val),8)})
    return pts


@router.get('/info')
def get_info():
    data = _load_data()
    B = data[:, 2]
    return {'nTotal': int(len(data)), 'rRange': [float(data[:,0].min()), float(data[:,0].max())],
            'zRange': [float(data[:,1].min()), float(data[:,1].max())],
            'bMin': float(B.min()), 'bMax': float(B.max()), 'bMean': float(B.mean()),
            'source': 'COMSOL 5.4  2D 轴对称', 'current': 100, 'unit': 'T', 'coordUnit': 'mm'}


@router.get('/field2d')
def get_field2d(n: int = Query(6000, ge=200, le=20000)):
    data = _load_data()
    B    = data[:, 2]
    return {'points': _sample_2d(data, n), 'nTotal': int(len(data)), 'nSampled': n,
            'bMin': float(B.min()), 'bMax': float(B.max()),
            'rMin': float(data[:,0].min()), 'rMax': float(data[:,0].max()),
            'zMin': float(data[:,1].min()), 'zMax': float(data[:,1].max()),
            'unit': 'T', 'label': 'B'}


@router.get('/field3d')
def get_field3d(
    n_base:   int = Query(2500, ge=100, le=5000),
    n_angles: int = Query(12,   ge=4,   le=36),
):
    data = _load_data()
    B    = data[:, 2]
    return {'points': _sample_3d(data, n_base, n_angles),
            'nTotal': int(len(data)), 'nSampled': n_base * n_angles,
            'bMin': float(B.min()), 'bMax': float(B.max()), 'unit': 'T', 'label': 'B'}

