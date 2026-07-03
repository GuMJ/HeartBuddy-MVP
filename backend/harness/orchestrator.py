"""ChatOrchestrator — 全流程编排器（V1.1 情绪识别 + 动态人设）"""

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
    """一次聊天请求的完整编排"""

    def __init__(self):
        self._agents = {"companion": CompanionAgent()}

    async def handle_chat(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[str]:
        broker = trace_broker

        # 1. 保存用户消息
        await context_manager.add_message(session_id, "user", user_message)
        await session_manager.increment_message_count(session_id)

        # 2. 感知：LLM 情绪检测 + 关键词降级
        context = await context_manager.get_messages(session_id)
        emotion, confidence, evidence = await emotion_detector.detect(user_message, context)
        await broker.trace("emotion.detected", session_id,
                           emotion=emotion, confidence=confidence, evidence=evidence,
                           method=emotion_detector.last_method)
        await broker.trace("agent.perceive", session_id,
                           emotion=emotion, confidence=confidence,
                           evidence=evidence, user_message=user_message,
                           method=emotion_detector.last_method)

        # 3. 决策：路由 + 引导判断
        decision = await route_engine.decide(
            session_id, user_message, emotion, confidence)
        await broker.trace("route.decision", session_id,
                           input=user_message,
                           matched_keywords=decision.matched_keywords,
                           selected_agent=decision.agent,
                           confidence=decision.confidence,
                           reason=decision.reason,
                           suggest_workflow=decision.suggest_workflow)

        agent = self._agents.get(decision.agent, self._agents["companion"])
        await broker.trace("agent.active", session_id,
                           agent_name=agent.agent_name, reason=decision.reason)

        # 4. Agent 自主选择技能
        always_skills = skill_manager.get_always_skills()
        on_demand = skill_manager.get_registry()
        selected_on_demand = await llm_client.select_skills(
            user_message, emotion, confidence, on_demand
        )
        selected_names = always_skills + selected_on_demand
        selected_files = skill_manager.get_source_files(selected_names)

        await broker.trace("agent.plan", session_id,
                           approach=f"Agent 选择了 {len(selected_names)} 个技能",
                           sources=selected_files,
                           skills=selected_names,
                           reasoning=f"情绪={emotion}, always={always_skills}, on_demand={selected_on_demand}")

        # 5. 行动：查 DB + 调 LLM
        estimated_tokens = sum(len(m["content"]) for m in context) // 2
        await broker.trace("db.query", session_id,
                           query_type="加载对话历史", result_count=len(context),
                           detail=f"messages 表 → {len(context)}条, ~{estimated_tokens}tokens")
        await broker.trace("context.loaded", session_id,
                           message_count=len(context), total_tokens_estimate=estimated_tokens)
        await broker.trace("agent.action", session_id,
                           action_type="调用 LLM",
                           detail=f"模型: {llm_client.model}, 上下文: {len(context)}条消息"
                                  f"{'（含深度思考）' if llm_client.is_reasoner else ''}")

        # 6. 流式处理 + 输出
        full_text = ""
        chunk_count = 0
        try:
            async for chunk_text in agent.process(
                user_message, context, session_id, broker,
                selected_skills=selected_names,
                emotion=emotion,
                confidence=confidence,
                suggest_workflow=decision.suggest_workflow,
            ):
                full_text += chunk_text
                chunk_count += 1
                yield _sse_event("sse.text_chunk",
                                 {"session_id": session_id, "content": chunk_text})
        except Exception as e:
            yield _sse_event("sse.error",
                             {"session_id": session_id, "error": "PROCESSING_ERROR", "message": str(e)})
            raise

        # 7. 观察：LLM 结果
        await broker.trace("agent.observe", session_id,
                           observation_type="LLM 调用完成",
                           summary=f"{chunk_count} chunks, 共{len(full_text)}字")

        # 8. 兜底：空回复或过短回复
        if len(full_text.strip()) < 1:
            full_text = "嗯，我再想想…"
            yield _sse_event("sse.text_chunk",
                             {"session_id": session_id, "content": full_text})

        # 9. 保存 + 完成
        message_id = await context_manager.add_message(session_id, "assistant", full_text)
        await broker.trace("sse.text_complete", session_id,
                           message_id=message_id, full_text=full_text)
        yield _sse_event("sse.text_complete",
                         {"session_id": session_id, "message_id": message_id, "full_text": full_text,
                          "emotion": emotion})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


orchestrator = ChatOrchestrator()
