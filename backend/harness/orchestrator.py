"""ChatOrchestrator — 全流程编排器（V1.1）"""

import json
from typing import AsyncIterator
from backend.harness.trace_broker import trace_broker
from backend.harness.router import route_engine
from backend.harness.context import context_manager
from backend.harness.session import session_manager
from backend.agents.companion import CompanionAgent
from backend.services.llm_client import llm_client
from backend.services.emotion_detector import emotion_detector
from backend.services.skill_manager import skill_manager


class ChatOrchestrator:

    def __init__(self):
        self._agents = {"companion": CompanionAgent()}

    async def handle_chat(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[str]:
        broker = trace_broker

        # 1. 加载历史（不含当前消息），保存用户消息
        history = await context_manager.get_messages(session_id)
        await context_manager.add_message(session_id, "user", user_message)
        await session_manager.increment_message_count(session_id)

        # 2. 感知：LLM 情绪检测
        emotion, confidence, _ = await emotion_detector.detect(user_message, history)
        # 技能选择：非 neutral → 加载 emotion-guide
        on_demand = ["情绪应对策略"] if emotion != "neutral" else []
        selected_names = skill_manager.get_always_skills() + on_demand

        # 感知
        await broker.trace("agent.perceive", session_id,
                           emotion=emotion, confidence=confidence,
                           user_message=user_message, method=emotion_detector.last_method)

        # 计划：情绪 + 技能
        selected_files = skill_manager.get_source_files(selected_names)
        await broker.trace("agent.plan", session_id,
                           skills=selected_files,
                           emotion=emotion, confidence=confidence)

        # 上下文
        await broker.trace("context.loaded", session_id,
                           history=len(history),
                           total=len(history) + 1)

        # 3. 决策 + 执行
        decision = await route_engine.decide(session_id, user_message, emotion, confidence)
        agent = self._agents.get(decision.agent, self._agents["companion"])

        full_text = ""
        try:
            async for chunk_text in agent.process(
                user_message, history, session_id, broker,
                selected_skills=selected_names,
                emotion=emotion, confidence=confidence,
            ):
                full_text += chunk_text
                yield _sse_event("sse.text_chunk",
                                 {"session_id": session_id, "content": chunk_text})
        except Exception as e:
            yield _sse_event("sse.error",
                             {"session_id": session_id, "error": "PROCESSING_ERROR", "message": str(e)})
            raise

        # 4. 兜底 + 保存
        if len(full_text.strip()) < 1:
            full_text = "嗯，我再想想…"
            yield _sse_event("sse.text_chunk",
                             {"session_id": session_id, "content": full_text})

        message_id = await context_manager.add_message(session_id, "assistant", full_text)
        await broker.trace("sse.text_complete", session_id,
                           message_id=message_id, full_text=full_text)
        yield _sse_event("sse.text_complete",
                         {"session_id": session_id, "message_id": message_id, "full_text": full_text})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


orchestrator = ChatOrchestrator()
