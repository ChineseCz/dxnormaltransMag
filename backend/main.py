"""
dx-platform  FastAPI 主应用入口
启动方式：
  开发：python run.py
  生产：uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth.routes import router as user_router
from api.data.routes import router as data_router
from api.data.dataset import router as dataset_router
from api.ml.model import router as model_router
from api.ml.predict import router as predict_router
from api.assistant.routes import router as ai_router
from api.devices.gaoya import router as gaoya_router
from api.devices.reactor import router as reactor_router
from api.devices.transfield import router as transfield_router
from api.files.routes import router as files_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时将残留的 training 状态标记为 failed，避免 DB 状态卡住"""
    try:
        from db_pg import get_conn
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("UPDATE t_model SET status='failed' WHERE status='training'")
        affected = cur.rowcount
        conn.commit()
        cur.close(); conn.close()
        if affected:
            print(f"[startup] 清理 {affected} 条残留 training 状态 → failed")
    except Exception as e:
        print(f"[startup] 清理残留训练状态失败（非致命）: {e}")
    yield  # 应用正常运行


app = FastAPI(
    title="dx-platform — 电气设备电磁场实时预测平台",
    version="2.0.0",
    description="基于 FastAPI + Celery 的异步微服务预测平台",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router,      prefix="/api/user",       tags=["用户鉴权"])
app.include_router(data_router,      prefix="/api/data",       tags=["数据处理"])
app.include_router(dataset_router,   prefix="/api/dataset",    tags=["数据集管理"])
app.include_router(model_router,     prefix="/api/model",      tags=["模型训练"])
app.include_router(predict_router,   prefix="/api/predict",    tags=["实时预测"])
app.include_router(ai_router,        prefix="/api/ai",         tags=["智能助手"])
app.include_router(files_router,     prefix="/api/files",      tags=["文件管理"])
app.include_router(gaoya_router,     prefix="/api/gaoya",      tags=["高压套管"])
app.include_router(reactor_router,   prefix="/api/reactor",    tags=["电抗器"])
app.include_router(transfield_router,prefix="/api/transfield", tags=["变压器电场"])


@app.get("/", tags=["健康检查"])
def index():
    return {"message": "Transformer Physical Field Platform API Service", "version": "2.0"}
