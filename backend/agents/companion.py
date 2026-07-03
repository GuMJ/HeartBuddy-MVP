"""CompanionAgent — 闲聊共情陪伴（V1.1 Skills 系统）"""

import time
from typing import AsyncIterator, Optional
from backend.agents.base import BaseAgent
from backend.harness.trace_broker import TraceBroker
from backend.services.llm_client import llm_client
from backend.services.skill_manager import skill_manager

SENTENCE_END = {"。", "！", "？", "\n"}
THINK_FLUSH_SIZE = 60


class CompanionAgent(BaseAgent):
    """温暖共情的闲聊陪伴 Agent"""

    agent_name = "companion"

    def build_prompt(self, selected_skills: list[str], emotion: str = "neutral",
                      confidence: float = 0.0, suggest_workflow: bool = False) -> str:
        """根据 Agent 自主选择的技能拼装系统提示"""
        base = skill_manager.load(selected_skills)

        # 情绪预检测结果（供 LLM 参考，可自行矫正）
        if emotion != "neutral":
            base += (
                f"\n\n## 情绪预检测\n"
                f"系统预判用户情绪为 {emotion}（程度 {confidence:.2f}/1.0）。"
                f"这只是参考，你可以根据对话内容自行矫正。\n"
            )

        if suggest_workflow and emotion == "anxious":
            base += (
                "\n【重要】本次回复末尾，请自然地说一句话引导用户尝试情绪急救工具。"
                "必须是自然的、不强迫的，像朋友推荐好用的东西一样。"
            )
        return base

    async def process(
        self,
        message: str,
        context: list[dict],
        session_id: str,
        broker: TraceBroker,
        selected_skills: Optional[list[str]] = None,
        emotion: str = "neutral",
        confidence: float = 0.0,
        suggest_workflow: bool = False,
    ) -> AsyncIterator[str]:
        if selected_skills is None:
            selected_skills = ["核心人格"]
        system_prompt = self.build_prompt(selected_skills, emotion, confidence, suggest_workflow)
        messages = [{"role": "system", "content": system_prompt}]
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
                                           duration_ms=round(think_duration_ms, 1))
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
