"""EmotionDetector — LLM 情绪分类 + 关键词降级"""

from typing import Optional
from backend.config import settings
from backend.services.llm_client import llm_client


FALLBACK_KEYWORDS: dict[str, list[str]] = {
    "anxious": ["紧张", "焦虑", "不安", "慌", "害怕", "担心", "忐忑", "恐慌",
                 "压力", "烦躁", "崩溃", "手心出汗", "坐立不安"],
    "sad": ["难过", "伤心", "哭", "低落", "沮丧", "失望", "孤独", "寂寞", "emo", "想哭"],
    "angry": ["生气", "愤怒", "讨厌", "烦", "恼火", "气死"],
    "happy": ["开心", "高兴", "快乐", "期待", "兴奋", "激动", "太好了"],
}

CLASSIFY_PROMPT = (
    "你是一个情绪识别专家。仔细阅读用户的话，感受其情绪状态。\n"
    "不要只看关键词，要关注：身体感受、情境描述、语气、隐含情绪。\n\n"
    "输出格式：emotion,confidence（0到1之间，1表示非常确定）\n"
    "emotion 可选：anxious / sad / angry / happy / neutral\n\n"
    "示例：\n"
    "用户：手心一直出汗，心跳好快 → anxious,0.9\n"
    "用户：啥都不想干 → sad,0.5\n"
    "用户：完全不想理那个人 → angry,0.7\n"
    "用户：今天天气不错 → neutral,0.9\n"
    "用户：有点烦但还好 → neutral,0.6\n\n"
)


class EmotionDetector:
    """情绪检测器：LLM 优先（用 deepseek-chat），失败降级到关键词"""

    def __init__(self):
        self._method = "llm"

    @property
    def last_method(self) -> str:
        return self._method

    async def detect(self, message: str, context: Optional[list[dict]] = None) -> tuple[str, float, str]:
        """检测用户情绪。返回 (emotion, confidence, evidence)"""
        try:
            result = await self._classify_with_llm(message, context)
            if result:
                self._method = "llm"
                return result
        except Exception:
            pass

        self._method = "keyword_fallback"
        return self._classify_with_keywords(message)

    async def _classify_with_llm(
        self, message: str, context: Optional[list[dict]] = None
    ) -> Optional[tuple[str, float, str]]:
        user_content = message
        if context:
            user_msgs = [m["content"] for m in context if m["role"] == "user"]
            recent = user_msgs[-2:]
            if recent:
                user_content = "\n".join(recent + [message])

        prompt = CLASSIFY_PROMPT + f"用户：{user_content}\n情绪："

        # 用 deepseek-chat 做分类（不用 reasoner，更快更可靠）
        response = await llm_client.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10,
        )

        raw = response.choices[0].message.content.strip().lower()
        valid = {"anxious", "sad", "angry", "happy", "neutral"}

        # 解析 "emotion,confidence" 格式
        parts = raw.replace("，", ",").split(",")
        emotion = parts[0].strip()
        confidence = 0.7  # 默认
        if len(parts) > 1:
            try:
                confidence = float(parts[1].strip())
            except ValueError:
                pass

        if emotion in valid:
            return emotion, confidence, f"LLM: {emotion},{confidence}"

        # 降级：从响应中提取有效值
        for v in valid:
            if v in emotion:
                return v, confidence, f"LLM: {raw} → {v}"

        return None

    @staticmethod
    def _classify_with_keywords(message: str) -> tuple[str, float, str]:
        for emotion, kws in FALLBACK_KEYWORDS.items():
            matched = [kw for kw in kws if kw in message]
            if matched:
                return emotion, min(len(matched) / 3, 1.0), "、".join(matched)
        return "neutral", 0.0, ""


emotion_detector = EmotionDetector()
