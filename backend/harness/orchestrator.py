"""ChatOrchestrator — 全流程编排器"""

import json
from typing import AsyncIterator
from backend.harness.trace_broker import trace_broker
from backend.harness.router import route_engine
from backend.harness.context import context_manager
from backend.harness.session import session_manager
from backend.agents.companion import CompanionAgent
from backend.agents.workflow import WorkflowAgent
from backend.services.llm_client import llm_client


class ChatOrchestrator:
    """一次聊天请求的完整编排"""

    def __init__(self):
        self._agents = {
            "companion": CompanionAgent(),
            "workflow": WorkflowAgent(),
        }

    async def handle_chat(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[str]:
        broker = trace_broker

        # 1. 保存用户消息
        await context_manager.add_message(session_id, "user", user_message)
        await session_manager.increment_message_count(session_id)

        # 2. 感知：情绪检测
        emotion, confidence, evidence = _detect_emotion(user_message)
        if emotion != "neutral":
            await broker.trace("emotion.detected", session_id,
                               emotion=emotion, confidence=confidence, evidence=evidence)
        await broker.trace("agent.perceive", session_id,
                           emotion=emotion, confidence=confidence,
                           evidence=evidence, user_message=user_message[:200])

        # 3. 决策：路由
        decision = await route_engine.decide(user_message)
        await broker.trace("route.decision", session_id,
                           input=user_message,
                           matched_keywords=decision.matched_keywords,
                           selected_agent=decision.agent,
                           confidence=decision.confidence,
                           reason=decision.reason)

        agent = self._agents.get(decision.agent, self._agents["companion"])
        await broker.trace("agent.active", session_id,
                           agent_name=agent.agent_name, reason=decision.reason)

        # 4. 观察：加载上下文
        context = await context_manager.get_messages(session_id)
        estimated_tokens = sum(len(m["content"]) for m in context) // 2
        await broker.trace("context.loaded", session_id,
                           message_count=len(context), total_tokens_estimate=estimated_tokens)
        await broker.trace("db.query", session_id,
                           query_type="加载对话历史", result_count=len(context),
                           detail=f"从 messages 表加载 {len(context)} 条消息，预估 {estimated_tokens} tokens")

        # 5. 计划
        approach = _describe_plan(decision.agent, emotion)
        await broker.trace("agent.plan", session_id,
                           approach=approach,
                           reasoning=f"路由={decision.agent}, 情绪={emotion}, 上下文={len(context)}条")

        # 6. 行动：调用 LLM
        await broker.trace("agent.action", session_id,
                           action_type="调用 LLM",
                           detail=f"模型: {llm_client.model}, 上下文: {len(context)}条消息"
                                  f"{'（含深度思考）' if llm_client.is_reasoner else ''}")

        # 7. 流式处理 + 输出
        full_text = ""
        chunk_count = 0
        try:
            async for chunk_text in agent.process(
                user_message, context, session_id, broker
            ):
                full_text += chunk_text
                chunk_count += 1
                yield _sse_event("sse.text_chunk",
                                 {"session_id": session_id, "content": chunk_text})
        except Exception as e:
            yield _sse_event("sse.error",
                             {"session_id": session_id, "error": "PROCESSING_ERROR", "message": str(e)})
            raise

        # 8. 观察：LLM 结果
        await broker.trace("agent.observe", session_id,
                           observation_type="LLM 调用完成",
                           summary=f"{chunk_count} chunks, 共{len(full_text)}字")

        # 9. 保存 + 完成
        message_id = await context_manager.add_message(session_id, "assistant", full_text)
        await broker.trace("sse.text_complete", session_id,
                           message_id=message_id, full_text=full_text)
        yield _sse_event("sse.text_complete",
                         {"session_id": session_id, "message_id": message_id, "full_text": full_text})


# ---- 辅助函数 ----

def _detect_emotion(message: str) -> tuple[str, float, str]:
    keywords = {
        "anxious": ["紧张", "焦虑", "不安", "慌", "害怕", "担心", "忐忑", "恐慌",
                     "压力", "烦躁", "崩溃", "手心出汗", "坐立不安"],
        "sad": ["难过", "伤心", "哭", "低落", "沮丧", "失望", "孤独", "寂寞", "emo", "想哭"],
        "angry": ["生气", "愤怒", "讨厌", "烦", "恼火", "气死"],
        "happy": ["开心", "高兴", "快乐", "期待", "兴奋", "激动", "太好了"],
    }
    for emotion, kws in keywords.items():
        matched = [kw for kw in kws if kw in message]
        if matched:
            return emotion, min(len(matched) / 3, 1.0), "、".join(matched)
    return "neutral", 0.0, ""


def _describe_plan(agent: str, emotion: str) -> str:
    if agent == "workflow":
        return "引导用户进入缓解紧张工作流：先采集2-3个问题，再匹配合适的放松方案"
    plans = {
        "anxious": "共情倾听，接纳用户的紧张情绪，温和引导用户多说一点",
        "sad": "温暖陪伴，先共情不急于解决，给用户安全的空间表达",
        "angry": "先接纳情绪不否定，帮助用户梳理愤怒的来源",
        "happy": "分享用户的喜悦，强化积极体验",
    }
    return plans.get(emotion, "温暖共情地陪伴用户闲聊，保持好奇和开放")


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# 模块级单例
orchestrator = ChatOrchestrator()
