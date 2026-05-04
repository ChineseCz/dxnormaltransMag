"""api/data/routes.py  ──  数据上传 & 预处理状态接口
NOTE: 下方 4 个旧路由（/upload/raw、/auto-detect、/processed-status、/execute）
      指向 core_algorithms 目录，前端已全部迁移到新的 /api/datasets/* 路由，
      此处保留注释以便追溯历史，不再注册到 FastAPI。
"""
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import numpy as np

try:
    from core_algorithms.preprocess.advanced_data_logic import analyze_data_quality, detect_steady_state
except ModuleNotFoundError:
    def analyze_data_quality(path: str) -> dict:
        return {"warning": "core_algorithms.preprocess 模块未安装"}
    def detect_steady_state(data) -> float:
        return 0.0

router = APIRouter()

_HERE    = os.path.dirname(os.path.abspath(__file__))   # api/data/
_BACKEND = os.path.dirname(os.path.dirname(_HERE))       # backend/
ROOT_DIR = os.path.dirname(_BACKEND)                     # project root

DATA_RAW_DIR   = os.path.join(ROOT_DIR, 'core_algorithms', 'data', 'raw data')
DATA_SPLIT_DIR = os.path.join(ROOT_DIR, 'core_algorithms', 'data', 'splited data')


class ExecuteRequest(BaseModel):
    type: str = ""


# ── 已废弃路由：前端不再调用，指向 core_algorithms 旧管线 ──────────────────
#
# @router.post('/upload/raw')
# async def upload_raw_data(file: UploadFile = File(...)):
#     """[DEAD] 上传原始数据到 core_algorithms/data/raw data/，前端已改用 /api/datasets/{id}/upload"""
#     filename = file.filename
#     if not filename:
#         return JSONResponse(status_code=400, content={"error": "No selected file"})
#     file_path = os.path.join(DATA_RAW_DIR, filename)
#     contents  = await file.read()
#     with open(file_path, 'wb') as fp:
#         fp.write(contents)
#     stats = analyze_data_quality(file_path)
#     return {"message": f"File {filename} uploaded successfully.", "analysis": stats, "filename": filename}
#
#
# @router.post('/auto-detect')
# def auto_detect_stable_point():
#     """[DEAD] 旧稳态检测，前端已改用 /api/datasets/{id}/auto-detect"""
#     filenames = os.listdir(DATA_RAW_DIR)
#     vol_file = next((f for f in filenames if 'vol' in f.lower() or 'cur' in f.lower()), None)
#     if not vol_file:
#         return JSONResponse(status_code=404, content={"error": "No voltage/current data found."})
#     file_path = os.path.join(DATA_RAW_DIR, vol_file)
#     data = np.loadtxt(file_path, encoding='utf-8', comments='%')[:, 1]
#     t0   = detect_steady_state(data)
#     return {"t0": t0, "suggested_msg": f"Detected steady state around {t0:.4f}s"}
#
#
# @router.get('/processed-status')
# def processed_data_status():
#     """[DEAD] 旧流水线状态，前端已改用 /api/datasets/{id}/status"""
#     DATA_DIR = os.path.join(ROOT_DIR, 'core_algorithms', 'data')
#     PCA_DIR  = os.path.join(ROOT_DIR, 'core_algorithms', 'pca result')
#     pipeline_files = {
#         'cut':    {'label': '稳态截取',      'files': ['cutInput.txt', 'cutOutput.txt']},
#         'split':  {'label': '训练/测试划分', 'files': ['trainInput.txt', 'trainOutput.txt',
#                                                         'testInput.txt', 'testOutput.txt']},
#         'pca':    {'label': 'PCA 降维',      'files': ['trainPCA.txt', 'testPCA.txt'],
#                    'extra_dir': PCA_DIR,     'extra_files': ['mean_pca.txt', 'vector_pca.txt']},
#         'zscore': {'label': 'Z-Score 归一化','files': ['zstrainInput.txt', 'zstestInput.txt',
#                                                         'zstrainPCA.txt', 'zstestPCA.txt']},
#     }
#     result = {}
#     for step, info in pipeline_files.items():
#         files_exist = all(os.path.isfile(os.path.join(DATA_DIR, f)) for f in info['files'])
#         if 'extra_dir' in info:
#             files_exist = files_exist and all(
#                 os.path.isfile(os.path.join(info['extra_dir'], f)) for f in info['extra_files']
#             )
#         result[step] = {'done': files_exist, 'label': info['label']}
#     train_info = {}
#     all_ready = result.get('zscore', {}).get('done', False) and result.get('pca', {}).get('done', False)
#     if all_ready:
#         try:
#             train_x = np.loadtxt(os.path.join(DATA_DIR, 'zstrainInput.txt'))
#             train_y = np.loadtxt(os.path.join(DATA_DIR, 'zstrainPCA.txt'))
#             test_x  = np.loadtxt(os.path.join(DATA_DIR, 'zstestInput.txt'))
#             train_info = {
#                 'trainSamples': int(train_x.shape[0]),
#                 'testSamples':  int(test_x.shape[0]),
#                 'inputDim':     int(train_x.shape[1]) if train_x.ndim > 1 else 1,
#                 'outputDim':    int(train_y.shape[1]) if train_y.ndim > 1 else 1,
#                 'trainRatio':   round(train_x.shape[0] / (train_x.shape[0] + test_x.shape[0]), 2),
#             }
#         except Exception:
#             pass
#     return {'pipeline': result, 'ready': all_ready, 'trainInfo': train_info}
#
#
# @router.post('/execute')
# def execute_processing(body: ExecuteRequest):
#     """[DEAD] 旧管线触发，前端已改用 /api/datasets/{id}/process"""
#     p_type = body.type
#     try:
#         import contextlib
#         @contextlib.contextmanager
#         def cd_preprocess():
#             old = os.getcwd()
#             os.chdir(os.path.join(ROOT_DIR, 'core_algorithms', 'preprocess'))
#             try:
#                 yield
#             finally:
#                 os.chdir(old)
#         with cd_preprocess():
#             if p_type == 'split':
#                 from core_algorithms.preprocess.splitData import splitFiles
#                 splitFiles()
#                 return {"status": "success", "msg": "数据物理步长切分完成"}
#             elif p_type == 'partition':
#                 from core_algorithms.preprocess.splitData import splitTrainTest, combineTrainTest
#                 splitTrainTest(); combineTrainTest()
#                 return {"status": "success", "msg": "数据样本拓扑划分成功"}
#             elif p_type == 'normalize':
#                 from core_algorithms.preprocess.splitData import indataNormalize
#                 indataNormalize()
#                 return {"status": "success", "msg": "归一化统计算子生成成功"}
#             elif p_type == 'pca':
#                 from core_algorithms.preprocess.splitData import outdataNormalize
#                 outdataNormalize()
#                 return {"status": "success", "msg": "PCA 线性流形投影成功"}
#         return {"status": "pending", "msg": f"Task {p_type} executed."}
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": str(e)})
