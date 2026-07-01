"""RouteEngine — 路由决策引擎

V1.0: 固定返回 companion，仅做关键词检测并记录到 trace。
V1.1: 接入情绪识别 + 意图分类，条件路由到 workflow。
V1.2: 完整上下文感知路由（情绪 + 状态机 + 用户历史）。
"""

from backend.shared.schemas import RouteDecision


class RouteEngine:
    """
    路由引擎 — 决定用户消息由哪个 Agent 处理。

    扩展方式（V1.1/V1.2）：
        - 注入 EmotionDetector 实例
        - 注入 IntentClassifier 实例
        - decide() 根据多信号综合判断
    """

    # 工作流关键词（V1.0 仅 trace 记录，V1.2 参与路由）
    WORKFLOW_KEYWORDS: list[str] = [
        "紧张", "焦虑", "压力", "放松", "缓解", "深呼吸",
        "睡不着", "心慌", "冥想", "冷静", "烦躁", "不安",
        "恐慌", "担忧", "害怕", "崩溃",
    ]

    async def decide(self, message: str) -> RouteDecision:
        """V1.0: 检测关键词但固定路由到 companion"""
        matched = [kw for kw in self.WORKFLOW_KEYWORDS if kw in message]

        return RouteDecision(
            agent="companion",  # V1.0 强制 companion
            matched_keywords=matched,
            confidence=min(len(matched) / 5, 1.0) if matched else 0.0,
            reason="v1.0_fallback",
        )


# 模块级单例
route_engine = RouteEngine()
