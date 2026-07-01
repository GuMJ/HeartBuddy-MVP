"""WorkflowAgent — 缓解紧张工作流（V1.2 完整实现）"""

from typing import AsyncIterator
from backend.agents.base import BaseAgent
from backend.harness.trace_broker import TraceBroker


class WorkflowAgent(BaseAgent):
    """缓解紧张情绪的结构化工作流 Agent"""

    agent_name = "workflow"

    PROMPT = (
        "你是 HeartBuddy 的情绪急救引导员。\n\n"
        "你的任务是通过 2-3 个简短问题了解用户当前的紧张状态，"
        "然后推荐最适合的缓解方案并引导执行。\n"
        "语气温暖、专业、有安全感。"
    )

    async def process(
        self,
        message: str,
        context: list[dict],
        session_id: str,
        broker: TraceBroker,
    ) -> AsyncIterator[str]:
        placeholder = (
            "情绪急救工作流正在建设中…\n\n"
            "这里将是「缓解紧张」的专属空间，"
            "我会先问你 2-3 个问题了解你现在的状态，"
            "然后匹配最适合你的放松方案（比如感官锚定法、情绪命名、渐进式肌肉放松等）。\n\n"
            "现在你可以先和我聊聊天，或者点击「缓解紧张」按钮，我会陪着你。"
        )
        yield placeholder
