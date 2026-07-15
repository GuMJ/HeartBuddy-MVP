"""EmotionDetector — LLM 情绪分类 + 关键词降级 + 工作流意图判断"""

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
    "分析用户情绪，判断是否需要进入工作流或直接使用某个方法。\n\n"
    "情绪：anxious / sad / angry / happy / neutral\n"
    "动作：none / 缓解紧张\n"
    "方法（仅动作=缓解紧张时需要，否则写 none）：\n"
    "  感官锚定法 / 情绪命名与抽屉法 / 渐进式肌肉放松 / 感恩速记 / 微型胜利法 / none\n\n"
    "规则：只有用户明确表达需要缓解紧张/焦虑时才 action=缓解紧张。只是在咨询信息、问方法是什么、描述症状但不求助时 action=none。用户自己已有放松计划（旅游、运动、聚会等）时 action=none，即使提到了紧张。只有说'教我/我想做/我要做/试试'具体方法时 method 才写具体方法名。\n\n"
    "参考：\n"
    "用户：今天面试好紧张，手心出汗 → anxious 0.9 none none\n"
    "用户：辗转反侧睡不着，翻来覆去 → anxious 0.8 缓解紧张 none\n"
    "用户：我最近压力太大了，有什么办法吗 → anxious 0.85 缓解紧张 none\n"
    "用户：教我54321 → anxious 0.8 缓解紧张 感官锚定法\n"
    "用户：我想做感官锚定 → anxious 0.8 缓解紧张 感官锚定法\n"
    "用户：肌肉放松有什么办法 → anxious 0.6 none none\n"
    "用户：有没有放松的方法 → anxious 0.75 缓解紧张 none\n"
    "用户：我要去三亚玩放松一下 → neutral 0.5 none none\n"
    "用户：我想去三亚玩放松放松，最近太紧张了 → anxious 0.6 none none\n"
    "用户：今天天气不错 → neutral 0.9 none none\n\n"
    "严格四行输出：\n"
    "emotion: anxious\n"
    "confidence: 0.85\n"
    "action: 缓解紧张\n"
    "method: 感官锚定法\n\n"
)


class EmotionDetector:

    def __init__(self):
        self._method = "llm"

    @property
    def last_method(self) -> str:
        return self._method

    async def detect(self, message: str, context=None) -> tuple[str, float, str, str, str]:
        try:
            result = await self._classify_with_llm(message, context)
            if result:
                self._method = "llm"
                return result
        except Exception:
            pass

        self._method = "keyword_fallback"
        e, c, ev = self._classify_with_keywords(message)
        return e, c, ev, "none", "none"

    async def _classify_with_llm(self, message, context=None):
        user_content = message
        if context:
            user_msgs = [m["content"] for m in context if m["role"] == "user"]
            recent = user_msgs[-2:]
            if recent:
                user_content = "\n".join(recent + [message])

        prompt = CLASSIFY_PROMPT + f"用户：{user_content}\n"

        response = await llm_client.client.chat.completions.create(
            model="deepseek-chat", temperature=0.1, max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content.strip()
        emotion, confidence, action, method = "neutral", 0.5, "none", "none"
        valid = {"anxious", "sad", "angry", "happy", "neutral"}
        method_map = {"感官锚定法": "sensory_anchor", "情绪命名与抽屉法": "emotion_naming",
                       "渐进式肌肉放松": "progressive_relaxation",
                       "感恩速记": "gratitude_snapshot", "微型胜利法": "micro_victory"}

        for line in raw.split("\n"):
            line = line.strip()
            if line.lower().startswith("emotion:"):
                e = line.split(":", 1)[1].strip().lower()
                if e in valid: emotion = e
            elif line.lower().startswith("confidence:"):
                try: confidence = float(line.split(":", 1)[1].strip())
                except ValueError: pass
            elif line.lower().startswith("action:"):
                action = line.split(":", 1)[1].strip()
                if action in ("none", "无"): action = "none"
            elif line.lower().startswith("method:"):
                m = line.split(":", 1)[1].strip()
                method = method_map.get(m, "none") if m != "none" else "none"

        return emotion, confidence, f"LLM: {raw[:40]}", action, method

    @staticmethod
    def _classify_with_keywords(message):
        for emotion, kws in FALLBACK_KEYWORDS.items():
            matched = [kw for kw in kws if kw in message]
            if matched:
                return emotion, min(len(matched) / 3, 1.0), "、".join(matched)
        return "neutral", 0.0, ""


emotion_detector = EmotionDetector()
