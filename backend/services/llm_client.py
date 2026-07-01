"""DeepSeek API 客户端 — 基于 OpenAI SDK 的流式调用封装

支持两种模型：
  - deepseek-chat (V3)：普通聊天，只有 content
  - deepseek-reasoner (R1)：深度思考，先出 reasoning_content 再出 content
"""

from typing import Optional, AsyncIterator, Literal, Tuple
from openai import AsyncOpenAI
from backend.config import settings

ChunkType = Literal["reasoning", "content"]


class LLMClient:
    """DeepSeek API 流式聊天客户端（延迟初始化）"""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self.model = settings.deepseek_model
        self._is_reasoner = "reasoner" in self.model

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )
        return self._client

    @property
    def is_reasoner(self) -> bool:
        """是否使用推理模型（有思考链）"""
        return self._is_reasoner

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[Tuple[ChunkType, str]]:
        """
        流式调用 DeepSeek chat/completions。

        Yields:
            ("reasoning", text) — 思考链内容（仅 reasoner 模型）
            ("content", text)   — 最终回复内容
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        # reasoner 模型不支持 temperature
        if not self._is_reasoner:
            kwargs["temperature"] = temperature or settings.llm_temperature
        if max_tokens or settings.llm_max_tokens:
            kwargs["max_tokens"] = max_tokens or settings.llm_max_tokens

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            delta = chunk.choices[0].delta

            # 推理模型的思考链
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield ("reasoning", reasoning)
                continue

            # 普通回复内容
            if delta.content:
                yield ("content", delta.content)


# 模块级单例
llm_client = LLMClient()
