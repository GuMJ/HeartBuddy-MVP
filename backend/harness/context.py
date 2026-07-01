"""ContextManager — 会话上下文拼装"""

from typing import Optional
from backend.config import settings
from backend.data import repository


class ContextManager:
    """管理对话上下文的读写"""

    async def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> list[dict]:
        """获取会话最近的消息列表"""
        limit = limit or settings.max_context_messages
        return await repository.get_messages(session_id, limit=limit)

    async def add_message(self, session_id: str, role: str, content: str) -> int:
        """保存消息，返回 message_id"""
        return await repository.save_message(session_id, role, content)

    async def get_conversation_text(self, session_id: str) -> str:
        """将最近消息拼接为纯文本字符串（供快速上下文参考）"""
        messages = await self.get_messages(session_id)
        lines = []
        for m in messages:
            role_label = "用户" if m["role"] == "user" else "HB"
            lines.append(f"{role_label}: {m['content']}")
        return "\n".join(lines)


# 模块级单例
context_manager = ContextManager()
