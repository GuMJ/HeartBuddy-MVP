"""RouteEngine — V1.2 路由（LLM 意图已在 emotion_detector 中判断）"""

from backend.shared.schemas import RouteDecision


class RouteEngine:

    async def decide(
        self, session_id: str, message: str, emotion: str, confidence: float,
        entry: str = "chat", action: str = "none", method: str = "none",
    ) -> RouteDecision:
        if entry == "button":
            return RouteDecision(agent="workflow", reason="button_click")

        if action != "none":
            return RouteDecision(
                agent="workflow", reason="llm_intent",
                skip_qa=method if method != "none" else None,
            )

        return RouteDecision(agent="companion", reason="companion_default")


route_engine = RouteEngine()
