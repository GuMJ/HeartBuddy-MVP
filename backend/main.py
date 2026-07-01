"""HeartBuddy — FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.data.db import init_db
from backend.api.chat import router as chat_router
from backend.api.monitor import router as monitor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    await init_db()
    yield


app = FastAPI(
    title="HeartBuddy API",
    description="AI 情感陪伴机器人 — MVP V1.0",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS（本地开发允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(monitor_router)


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok", "version": "1.0.0"}
