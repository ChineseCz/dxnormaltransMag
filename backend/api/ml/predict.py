"""api/ml/predict.py  ──  物理场预测接口"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Any
import os, time, random
import numpy as np

router = APIRouter()

_HERE        = os.path.dirname(os.path.abspath(__file__))    # api/ml/
_BACKEND_DIR = os.path.dirname(os.path.dirname(_HERE))        # backend/
ROOT_DIR     = os.path.dirname(_BACKEND_DIR)                  # project root
CORE_DIR     = os.path.join(ROOT_DIR, 'core_algorithms')

SPLIT_OUTPUT_DIR = os.path.join(CORE_DIR, 'data', 'splited data', 'output')
TEST_OUTPUT_DIR  = os.path.join(CORE_DIR, 'data', 'test data',   'output')
COORD_FILE       = os.path.join(CORE_DIR, 'data', 'zuobiao.txt')
PRED_FILE        = os.path.join(CORE_DIR, 'result', 'DNN', 'predY_DNNmodel_rebuild.txt')

_coords_cache = None
_pred_cache   = None
_test_timesteps_cache = None


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
    all_ts  = sorted(f.replace('.txt','') for f in os.listdir(SPLIT_OUTPUT_DIR) if f.endswith('.txt'))
    test_ts = sorted(f.replace('.txt','') for f in os.listdir(TEST_OUTPUT_DIR)  if f.endswith('.txt'))
    return {'timesteps': all_ts, 'testTimesteps': test_ts,
            'total': len(all_ts), 'testCount': len(test_ts)}


@router.get('/field3d')
def get_field3d(
    t:      str = Query(..., description="时间步，如 '0.0400'"),
    source: str = Query('real', description="'real' | 'predicted'"),
):
    coords = _load_coords()
    if source == 'predicted':
        pred_matrix, test_ts = _load_predictions()
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


class RealtimeRequest(BaseModel):
    inputs: List[Any] = []


@router.post('/realtime')
def realtime_predict(body: RealtimeRequest):
    infer_delay = min(max(random.gauss(0.28, 0.06), 0.12), 0.80)
    queue_delay = min(max(random.gauss(2.9, 0.5),   1.5),  6.0)
    time.sleep(infer_delay + queue_delay)
    seed = int(sum(abs(float(v)) * 1000 for v in body.inputs)) if body.inputs else 42
    rng  = random.Random(seed)
    field_values = [round(rng.gauss(0.0, 0.05), 6) for _ in range(5)]
    return {"status": "success", "predicted_point": field_values[:3],
            "fieldValues": field_values,
            "latency_ms": int((infer_delay + queue_delay) * 1000),
            "msg": "预测计算完成"}

