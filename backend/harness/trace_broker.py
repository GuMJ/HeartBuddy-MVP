"""TraceBroker — 发布-订阅总线，双路实时分发 trace 事件"""

import asyncio
from backend.shared.schemas import TraceEvent

# 不推送到 WS 的事件（仅写日志）
_SILENT_FOR_WS = {"llm.response_chunk", "sse.text_chunk"}


class TraceBroker:
    """单进程内 asyncio.Queue Pub/Sub"""

    def __init__(self, logger=None):
        self._sse_queues: list[asyncio.Queue] = []
        self._ws_queues: list[asyncio.Queue] = []
        self._logger = logger

    # ---- 订阅管理 ----

    def subscribe_sse(self, q: asyncio.Queue) -> None:
        self._sse_queues.append(q)

    def unsubscribe_sse(self, q: asyncio.Queue) -> None:
        if q in self._sse_queues:
            self._sse_queues.remove(q)

    def subscribe_ws(self, q: asyncio.Queue) -> None:
        self._ws_queues.append(q)

    def unsubscribe_ws(self, q: asyncio.Queue) -> None:
        if q in self._ws_queues:
            self._ws_queues.remove(q)

    # ---- 通用 trace 方法（替代 18 个工厂方法） ----

    async def trace(self, event_type: str, session_id: str, **data) -> None:
        """推送一条 trace 事件到所有订阅者"""
        event = TraceEvent(type=event_type, session_id=session_id, data=data)

        if self._logger:
            self._logger.write(event_type, session_id, **data)

        if event_type not in _SILENT_FOR_WS:
            for q in self._ws_queues:
                await q.put(event)

        if event_type.startswith("sse."):
            for q in self._sse_queues:
                await q.put(event)


# 模块级单例
from backend.services.logger import logger  # noqa: E402
trace_broker = TraceBroker(logger=logger)
