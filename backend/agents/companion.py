"""CompanionAgent — 闲聊共情陪伴"""

import time
from typing import AsyncIterator
from backend.agents.base import BaseAgent
from backend.harness.trace_broker import TraceBroker
from backend.services.llm_client import llm_client

SENTENCE_END = {"。", "！", "？", "\n"}
THINK_FLUSH_SIZE = 60


class CompanionAgent(BaseAgent):
    """温暖共情的闲聊陪伴 Agent"""

    agent_name = "companion"

    PROMPT = (
        "你是 HeartBuddy，一个温暖、善解人意的 AI 情感陪伴伙伴。\n\n"
        "对话原则：\n"
        "1. 用 2-4 句话回复，语气自然，像朋友在聊天。\n"
        "2. 先共情，再回应。不否定用户的感受，不随意给建议。\n"
        "3. 如果用户表达了负面情绪，先接纳（\"听起来你最近确实挺难的…\"），不急于解决。\n"
        "4. 保持好奇和开放，引导用户多说一点，但不过度追问。\n"
        "5. 可以适当使用 emoji 增加亲和力，但不过度使用（每条消息最多 1-2 个）。\n"
        "6. 避免说教、鸡汤和空洞的安慰（\"一切都会好起来的\"）。\n"
        "7. 你不是心理咨询师，如果用户表现出严重心理健康问题，建议寻求专业帮助。"
    )

    async def process(
        self,
        message: str,
        context: list[dict],
        session_id: str,
        broker: TraceBroker,
    ) -> AsyncIterator[str]:
        messages = [{"role": "system", "content": self.PROMPT}]
        messages.extend(context)
        messages.append({"role": "user", "content": message})

        await broker.trace("llm.request", session_id,
                           model=llm_client.model,
                           messages=[{"role": m["role"], "content": m["content"][:200]}
                                     for m in messages])

        content_idx = 0
        think_idx = 0
        think_buffer = ""
        is_thinking = False
        start_time = time.time()

        try:
            async for chunk_type, chunk_text in llm_client.chat_stream(messages):
                if chunk_type == "reasoning":
                    if not is_thinking:
                        is_thinking = True
                        await broker.trace("agent.think.start", session_id)
                    think_buffer += chunk_text
                    if chunk_text and chunk_text[-1] in SENTENCE_END or len(think_buffer) >= THINK_FLUSH_SIZE:
                        think_idx += 1
                        await broker.trace("agent.think.chunk", session_id,
                                           chunk_index=think_idx, content=think_buffer)
                        think_buffer = ""
                else:
                    if is_thinking:
                        if think_buffer.strip():
                            think_idx += 1
                            await broker.trace("agent.think.chunk", session_id,
                                               chunk_index=think_idx, content=think_buffer)
                        think_duration_ms = (time.time() - start_time) * 1000
                        await broker.trace("agent.think.complete", session_id,
                                           total_chunks=think_idx,
                                           duration_ms=round(think_duration_ms, 1),
                                           preview="")
                        is_thinking = False
                        think_buffer = ""

                    content_idx += 1
                    await broker.trace("llm.response_chunk", session_id,
                                       chunk_index=content_idx, content=chunk_text)
                    yield chunk_text

        except Exception as e:
            await broker.trace("sse.error", session_id, error="LLM_ERROR", message=str(e))
            raise

        duration_ms = (time.time() - start_time) * 1000
        await broker.trace("llm.response_complete", session_id,
                           total_chunks=content_idx,
                           duration_ms=round(duration_ms, 1),
                           finish_reason="stop")
