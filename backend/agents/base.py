"""BaseAgent — Agent 抽象基类"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from backend.harness.trace_broker import TraceBroker


class BaseAgent(ABC):
    """
    Agent 基类，定义统一的 process() 接口。

    子类需实现：
        - agent_name: 标识名
        - system_prompt: 系统提示词（或动态生成的方法）
        - process(): 处理用户消息，流式产出回复文本
    """

    @property
    @abstractmethod
    def agent_name(self) -> str:
        ...

    async def get_system_prompt(self, session_id: str) -> str:
        """子类可覆写以支持动态提示词（V1.1+）"""
        return ""

    @abstractmethod
    async def process(
        self,
        message: str,
        context: list[dict],
        session_id: str,
        broker: TraceBroker,
    ) -> AsyncIterator[str]:
        """
        处理用户消息，流式产出回复文本。

        Args:
            message: 用户最新消息
            context: 历史消息列表 [{"role": "user"/"assistant", "content": "..."}]
            session_id: 会话 ID
            broker: TraceBroker 实例，用于推送 trace 事件

        Yields:
            str: 回复文本的每个增量片段
        """
        ...
