"""HeartBuddy 共享数据模型 — 所有 Pydantic schemas 的单一真相源"""

from pydantic import BaseModel, Field
from typing import Literal, Any, Optional
from datetime import datetime, timezone


# ============================================================
# 聊天
# ============================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=2000)
    entry: str = "chat"  # "chat" | "button"


class ChatResponse(BaseModel):
    session_id: str


# ============================================================
# 会话
# ============================================================

class SessionCreateResponse(BaseModel):
    session_id: str


class SessionInfo(BaseModel):
    id: str
    created_at: str
    updated_at: str
    status: Literal["active", "ended"]
    message_count: int


# ============================================================
# 路由
# ============================================================

class RouteDecision(BaseModel):
    agent: Literal["companion", "workflow"]
    confidence: float = 0.0
    reason: str = "v1.0_fallback"
    skip_qa: Optional[str] = None


# ============================================================
# Agent
# ============================================================

AgentName = Literal["companion", "workflow"]


# ============================================================
# 情绪（V1.1 激活，V1.0 仅 trace 记录）
# ============================================================

class EmotionLabel(BaseModel):
    emotion: Literal["anxious", "sad", "angry", "happy", "neutral"]
    confidence: float = 0.0
    evidence: str = ""


# ============================================================
# Trace 事件（统一信封）
# ============================================================

class TraceEvent(BaseModel):
    type: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    session_id: str
    data: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# SSE 负载（推送到手机端）
# ============================================================

class SSETextChunk(BaseModel):
    session_id: str
    content: str


class SSETextComplete(BaseModel):
    session_id: str
    message_id: int
    full_text: str


class SSEError(BaseModel):
    session_id: str
    error: str
    message: str
