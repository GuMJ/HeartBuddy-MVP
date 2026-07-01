"""数据访问层 — 会话与消息的 CRUD 操作"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from backend.data.db import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def create_session() -> str:
    """创建新会话，返回 session_id"""
    session_id = uuid.uuid4().hex[:12]
    async with get_db() as db:
        await db.execute(
            "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
            (session_id, _now(), _now()),
        )
    return session_id


async def end_session(session_id: str) -> None:
    """结束会话"""
    async with get_db() as db:
        await db.execute(
            "UPDATE sessions SET status = 'ended', updated_at = ? WHERE id = ?",
            (_now(), session_id),
        )


async def save_message(session_id: str, role: str, content: str) -> int:
    """保存消息，返回 message_id"""
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        await db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (_now(), session_id),
        )
        return cursor.lastrowid


async def get_messages(session_id: str, limit: int = 20) -> list[dict]:
    """获取会话最近的 N 条消息"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]


async def get_session(session_id: str) -> Optional[dict]:
    """获取会话信息"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, created_at, updated_at, status FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "status": row["status"],
        }
