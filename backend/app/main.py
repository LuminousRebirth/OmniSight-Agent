"""FastAPI 应用装配（T0-4）：建表 + 种子注入 + 路由注册。

启动流程（lifespan）：
1. init_db() 建全部 28 张表
2. seed_all() 注入种子数据（幂等）
3. 注册 /api/models*、/api/tasks 路由
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .agent.routes import router as agent_router
from .core.database import SessionLocal, init_db
from .core.seed import seed_all, seed_report
from .datasets.routes import router as tasks_router
from .detection.live import router as live_router
from .detection.routes import router as detect_router
from .model_lifecycle.routes import router as model_router
from .routing.routes import router as route_router
from .system.auth import router as auth_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seeded = seed_all(db)
        print(f"[startup] 建表完成; 种子注入={seeded}; {seed_report(db)}")
    finally:
        db.close()
    yield


app = FastAPI(title="OmniSight-Agent", version="0.1.0", lifespan=lifespan)

app.include_router(model_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(detect_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.include_router(route_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    """基础健康检查（Phase 3 完善组件级状态）"""
    return {"status": "ok"}
