"""SessionManager — 会话生命周期管理"""

from datetime import datetime, timezone
from typing import Optional
from backend.data import repository
from backend.harness.trace_broker import trace_broker


class SessionManager:
    """管理会话的创建、查询、结束"""

    def __init__(self):
        self._active: dict[str, dict] = {}

    async def create(self) -> str:
        session_id = await repository.create_session()
        self._active[session_id] = {
            "created_at": datetime.now(timezone.utc),
            "message_count": 0,
        }
        await trace_broker.trace("session.created", session_id)
        return session_id

    async def get(self, session_id: str) -> Optional[dict]:
        if session_id in self._active:
            return self._active[session_id]
        sess = await repository.get_session(session_id)
        if sess:
            self._active[session_id] = sess
        return sess

    async def exists(self, session_id: str) -> bool:
        if session_id in self._active:
            return self._active[session_id].get("status", "active") == "active"
        sess = await repository.get_session(session_id)
        return sess is not None and sess.get("status") == "active"

    async def increment_message_count(self, session_id: str) -> None:
        if session_id in self._active:
            self._active[session_id]["message_count"] = \
                self._active[session_id].get("message_count", 0) + 1

    async def end(self, session_id: str) -> None:
        await repository.end_session(session_id)
        if session_id in self._active:
            self._active[session_id]["status"] = "ended"
        created = self._active.get(session_id, {}).get("created_at")
        duration = 0.0
        if isinstance(created, datetime):
            duration = (datetime.now(timezone.utc) - created).total_seconds()
        await trace_broker.trace("session.ended", session_id, duration_seconds=duration)


session_manager = SessionManager()
