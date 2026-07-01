"""WS /ws/monitor — WebSocket 实时推送完整 trace 到监控面板"""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.harness.trace_broker import trace_broker

router = APIRouter()


@router.websocket("/ws/monitor")
async def monitor(websocket: WebSocket):
    """
    WebSocket 端点 — 实时接收所有 TraceEvent。

    连接后自动接收所有广播的 trace 事件（JSON 格式）。
    V1.0 单向推送（服务端 → 客户端），V1.1+ 可选支持客户端 filter 命令。
    """
    await websocket.accept()

    queue = asyncio.Queue()
    trace_broker.subscribe_ws(queue)

    try:
        while True:
            event = await queue.get()
            try:
                await websocket.send_text(event.model_dump_json())
            except Exception:
                # 客户端断开或发送失败
                break
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        trace_broker.unsubscribe_ws(queue)
