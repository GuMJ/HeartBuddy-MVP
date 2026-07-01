"""POST /api/chat — SSE 流式返回 AI 回复"""

import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.shared.schemas import ChatRequest
from backend.harness.orchestrator import orchestrator
from backend.harness.session import session_manager

router = APIRouter()


@router.post("/api/chat")
async def chat(req: ChatRequest):
    """
    发送消息并获取 AI 流式回复（SSE）。

    请求体：
        {"session_id": "...", "message": "..."}

    响应（SSE 流）：
        event: sse.text_chunk     data: {"session_id":"...","content":"..."}
        event: sse.text_complete  data: {"session_id":"...","message_id":42,"full_text":"..."}
        event: sse.error          data: {"session_id":"...","error":"...","message":"..."}
    """
    # 验证会话存在
    if not await session_manager.exists(req.session_id):
        raise HTTPException(status_code=404, detail=f"会话 {req.session_id} 不存在或已结束")

    async def event_stream():
        try:
            async for sse_event in orchestrator.handle_chat(
                req.session_id, req.message
            ):
                yield sse_event
        except Exception as e:
            yield f"event: sse.error\ndata: {json.dumps({'session_id': req.session_id, 'error': 'STREAM_ERROR', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


@router.post("/api/sessions")
async def create_session():
    """创建新会话，返回 session_id"""
    session_id = await session_manager.create()
    return {"session_id": session_id}
