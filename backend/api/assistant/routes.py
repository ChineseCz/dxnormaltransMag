"""api/assistant/routes.py  ──  智能助手问答接口"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time, random, hashlib

router = APIRouter()

_MOCK_ANSWERS = [
    "根据知识图谱分析，铁心电抗器在额定工况下中部绕组磁通密度偏低约12%，判断为中部匝间短路风险。",
    "DNN模型在当前测试集上MAE为2.29×10⁻²T，MAPE为2.37%，R²为0.990，预测精度满足工程要求。",
    "建议对低电流区间（100~300A）进行数据增强，以插值方式扩充稀疏样本，可有效降低该区段MAPE。",
    "根据DL/T 617-2021规程，铁心电抗器绕组温升不得超过65K，气隙磁密不得超过设计值的110%。",
    "频率响应分析（FRA）相关系数R低于0.98时，判定绕组存在形变或匝间短路，需结合直流电阻综合判定。",
]


class ChatRequest(BaseModel):
    session_id: str = "anon"
    message: str = ""


@router.post('/chat')
def chat(body: ChatRequest):
    if not body.message:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '消息不能为空'})

    delay      = min(max(random.gauss(2.0, 0.35), 1.2), 3.5)
    t0         = time.time()
    time.sleep(delay)
    elapsed_ms = int((time.time() - t0) * 1000)
    idx        = int(hashlib.md5(body.message.encode()).hexdigest(), 16) % len(_MOCK_ANSWERS)
    answer     = _MOCK_ANSWERS[idx]

    return {'code': 200, 'session_id': body.session_id, 'answer': answer,
            'latency_ms': elapsed_ms, 'tokens': len(answer), 'source': 'knowledge_base'}


@router.get('/health')
def health():
    return {'status': 'ok', 'model': 'Qwen3-8B', 'mode': 'simulated'}

