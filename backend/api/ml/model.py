"""api/ml/model.py  ──  模型训练接口"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

router = APIRouter()

_HERE    = os.path.dirname(os.path.abspath(__file__))   # api/ml/
_BACKEND = os.path.dirname(os.path.dirname(_HERE))       # backend/
ROOT_DIR = os.path.dirname(_BACKEND)                     # project root
MODEL_DIR = os.path.join(ROOT_DIR, 'core_algorithms', 'model')


class TrainRequest(BaseModel):
    model_type: str = "DNN"


@router.get('/list')
def list_models():
    try:
        files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pth')]
        return files
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post('/train')
def train_model(body: TrainRequest):
    """触发模型训练（待接入 Celery 异步队列）"""
    return {"status": "starting", "msg": f"正在启动 {body.model_type} 模型训练任务..."}

