"""HeartBuddy 共享数据模型 — 所有 Pydantic schemas 的单一真相源"""

from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime, timezone


# ============================================================
# 聊天
# ============================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=2000)


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
    matched_keywords: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    reason: str = "v1.0_fallback"
    suggest_workflow: bool = False


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
# 工作流状态（V1.2 激活，V1.0 占位）
# ============================================================

WorkflowState = Literal["idle", "assessing", "executing", "following_up", "closed"]


# ============================================================
# 方案（V1.2 使用，V1.0 硬编码占位）
# ============================================================

class SolutionPlan(BaseModel):
    id: str
    name: str
    description: str
    suitable_emotions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int = 5


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
