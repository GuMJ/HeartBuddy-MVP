"""RouteEngine — 路由决策引擎（V1.1 情绪感知 + 引导判断）"""

from backend.shared.schemas import RouteDecision


class RouteEngine:
    """
    路由引擎 — 根据用户消息和情绪状态决定 Agent 行为。

    V1.1: 情绪感知 + 引导判断（不切换 Agent）
    V1.2: 完整路由（状态机 + workflow 切换）
    """

    WORKFLOW_KEYWORDS = [
        "紧张", "焦虑", "压力", "放松", "缓解", "深呼吸",
        "睡不着", "心慌", "冥想", "冷静", "烦躁", "不安",
        "恐慌", "担忧", "害怕", "崩溃",
    ]

    async def decide(
        self, session_id: str, message: str, emotion: str, confidence: float
    ) -> RouteDecision:
        """根据情绪和上下文做路由决策"""
        matched = [kw for kw in self.WORKFLOW_KEYWORDS if kw in message]

        suggest = emotion == "anxious" and confidence > 0.6

        return RouteDecision(
            agent="companion",
            matched_keywords=matched,
            confidence=min(confidence, 1.0) if matched else 0.0,
            reason="emotion_guided" if suggest else "keyword_matched" if matched else "v1.0_fallback",
            suggest_workflow=suggest,
        )

route_engine = RouteEngine()
