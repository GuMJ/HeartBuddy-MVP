"""WorkflowAgent — 缓解紧张结构化工作流（V1.2）"""

import re
from typing import AsyncIterator, Optional

# 预编译正则 + 分隔符归一化
_DIGITS_RE = re.compile(r'\b\d+\b')

def _norm_sep(text: str) -> str:
    """中文顿号、全角逗号 → 英文逗号"""
    return text.replace("、", ",").replace("，", ",")
from backend.agents.base import BaseAgent
from backend.harness.trace_broker import TraceBroker
from backend.data.solutions import SOLUTIONS
from backend.services.llm_client import llm_client

MATCH_RULES = {
    ("A", "A", ""):  ["sensory_anchor"],
    ("A", "B", ""):  ["emotion_naming"],
    ("B", "A", "A"): ["micro_victory", "sensory_anchor"],
    ("B", "A", "B"): ["progressive_relaxation"],
    ("B", "B", "A"): ["micro_victory", "emotion_naming"],
    ("B", "B", "B"): ["gratitude_snapshot", "emotion_naming"],
}

GREETINGS = [
    "好的，我来陪你放松一下。先问问你，你感觉是快要爆炸了，还是一直提不起劲？",
    "我们一起来试试。先问问你，你感觉是快要爆炸了，还是一直提不起劲？",
    "好呀，让我帮你找找适合的方法。你感觉是快要爆炸了，还是一直提不起劲？",
    "没问题，几分钟就好。你感觉是快要爆炸了，还是一直提不起劲？",
]

# 执行方案时用户反馈的过渡处理：设置 awaiting 后由 _handle_awaiting 接管
AWAIT_CONTEXT = "换个方案还是继续当前步骤"
FOLLOW_UP_MSG = "感觉怎么样？如果 0-10 打分，开始前和结束后分别是多少呢？"

FEEDBACK_PROMPTS = {
    "worse": ("用户正在执行方案「{name}」，当前步骤：{step}。\n"
              "用户反馈（感觉更差/抗拒/很累/觉得不适合）：{msg}\n"
              "请温和回应1-2句：先接纳感受、不否定不鸡汤，然后自然地问要不要换个方案还是继续这个。"),
    "failed": ("用户正在执行方案「{name}」，当前步骤：{step}。\n"
               "用户反馈（尝试了但没做到/中途放弃）：{msg}\n"
               "请温和回应1-2句：告诉用户做不到很正常不用自责，然后自然地问要不要换个方案还是继续这个。"),
    "other": ("用户正在执行「{name}」（{desc}），当前步骤：{step}。\n"
              "用户说：{msg}\n"
              "请先简短回应或回答用户说的话（1-2句，自然友善），然后问'想继续方案还是聊聊天？'"),
}

# 线性方案意图检测 prompt（感官锚定、情绪命名、肌肉放松、微型胜利）
# LLM 只输出完成了哪些步或跳转目标，代码负责计算目标步序号
LINEAR_INTENT_PROMPT = (
    "方案步骤清单：\n{steps_list}\n\n"
    "用户当前在第 [{s_step}] 步（{step_name}）。\n"
    "系统上一句：{last_bot}\n"
    "用户说：{msg}\n\n"
    "判断用户意图（按优先级）：\n\n"
    "1. ⚠️ 跳转指令（最高优先级）— 用户要求去某个特定步骤：\n"
    "   回退：「回到XX」「重新XX」「再试一下上一步」「刚才那步再做一次」\n"
    "   前跳：「直接做XX」「跳过这步」「下一步」\n"
    "   重做：「重做XX」「这步再来一次」\n"
    "   → 全部输出 jump:目标步序号\n"
    "   只要用户表达了要回到/重做/重新/再试某个步骤，就是 jump。根据步骤清单判断目标步是哪个。\n\n"
    "⚠️ 枚举类步骤（看/触摸/听/闻/尝）：用户是在列东西回答提问，不是在报步骤完成。用户说的数字是物品数量，不是步骤序号。这类步骤永远输出 current。\n\n"
    "2. 推进类步骤（肌肉放松等）：用户表示完成了某些步骤 → 列出这些步骤的序号（逗号分隔）：\n"
    "   例：在[2]腿部，用户说「腿和腹都做好了」→ 2,3\n"
    "   例：在[4]手臂，用户说「手和肩膀、脸也都做好了」→ 4,5,6\n"
    "   例：用户只说「做好了」「好了」「继续」→ current\n\n"
    "3. 用户要退出（仅当明确要结束，且无跳转/重做信号）：\n"
    "   「不想做了」「先这样吧」「结束吧」→ quit\n\n"
    "4. 其他意图：\n"
    "   - stuck：卡住了、不知道怎么操作、提问\n"
    "   - worse：感觉更差、抗拒、很累、觉得不适合\n"
    "   - failed：尝试了但做不到、中途放弃\n"
    "   - other：闲聊、吐槽、玩笑\n\n"
    "简称映射（仅肌肉放松）：手/手臂/胳膊=手臂 腿/大腿/小腿=腿部 脚/脚趾/脚掌=脚部 腹/腹肌/肚子=腹部 肩/肩膀/肩颈=肩颈 脸/面部/面孔=面部\n\n"
    "严格只输出以下之一，不要输出任何其他文字：jump:N / current / quit / stuck / worse / failed / other / 步骤序号（逗号分隔）"
)

# 感恩速记意图检测 prompt — LLM 只做语义提取，代码做决策
GRATITUDE_INTENT_PROMPT = (
    "当前步骤：{step_name}\n"
    "系统上一句：{last_bot}\n"
    "用户说：{msg}\n\n"
    "判断这句话包含了什么信息（逗号分隔，可多个）：\n"
    "- event：说了新的事件（如「认识了新邻居」「考证通过了」「完成了画稿」）\n"
    "- feeling：表达了感受或情绪（如「好开心」「暖暖的」「感觉被接纳了」「充满希望」）\n"
    "- credit：说了自己做对了什么、功劳（如「主动打了招呼」「努力复习了」「坚持每天画五分钟」）\n"
    "- done：表示没有了、就这些、结束\n"
    "- more：说还有/继续，没给具体内容\n"
    "- other：无关话题\n\n"
    "只输出检测到的类型，逗号分隔。例如：event,feeling 或 feeling 或 done"
)


class WorkflowAgent(BaseAgent):
    agent_name = "workflow"
    _greet_idx = 0  # 类变量，跨会话轮换

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def is_closed(self, sid: str) -> bool:
        s = self._sessions.get(sid)
        return s is not None and s["phase"] == "closed"

    def _init(self, sid: str, skip_qa: Optional[str] = None):
        self._sessions[sid] = {
            "phase": "entering", "q1": "", "q2": "", "q3": "",
            "current_q": "q1", "matched": [], "plan_idx": 0, "step": 0,
            "skip_qa": skip_qa, "awaiting": None,
            "last_bot_msg": "",  # 上一轮系统回复，给意图检测当上下文
        }
        WorkflowAgent._greet_idx = (WorkflowAgent._greet_idx + 1) % len(GREETINGS)

    def _match(self, q1, q2, q3):
        key = (q1, q2, q3)
        if key in MATCH_RULES: return MATCH_RULES[key]
        for k, v in MATCH_RULES.items():
            if k[0] == q1 and k[1] == q2: return v
        for k, v in MATCH_RULES.items():
            if k[0] == q1: return v
        return ["sensory_anchor"]

    def _get_plan(self, pid: str) -> Optional[dict]:
        for p in SOLUTIONS:
            if p["id"] == pid: return p
        return None

    async def _llm(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 20) -> str:
        resp = await llm_client.client.chat.completions.create(
            model="deepseek-chat", temperature=temperature, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content.strip()

    async def _llm_long(self, prompt: str) -> str:
        return await self._llm(prompt, temperature=0.7, max_tokens=200)

    # ================================================================
    #  主入口
    # ================================================================
    async def process(self, message, context, session_id, broker, **kwargs):
        if session_id not in self._sessions or self._sessions[session_id]["phase"] == "closed":
            self._init(session_id, kwargs.get("skip_qa"))
        s = self._sessions[session_id]
        msg = message.strip()

        # 通用决策等待
        if s.get("awaiting"):
            async for c in self._handle_awaiting(session_id, msg, s, broker): yield c
            return

        if s["phase"] == "entering":
            s["phase"] = "assessing"
            if s.get("skip_qa"):
                # 直接进入指定方法，跳过 Q&A
                async for c in self._assess(session_id, msg, s, broker): yield c
            else:
                greet = GREETINGS[self._greet_idx]
                self._greet_idx = (self._greet_idx + 1) % len(GREETINGS)
                await broker.trace("workflow.state_change", session_id, phase="assessing")
                yield greet
            return
        if s["phase"] == "assessing":
            async for c in self._assess(session_id, msg, s, broker): yield c
        elif s["phase"] == "presenting":
            async for c in self._presenting(session_id, msg, s, broker): yield c
        elif s["phase"] == "executing":
            async for c in self._executing(session_id, msg, s, broker): yield c
        elif s["phase"] == "following_up":
            s["phase"] = "closed"
            yield FOLLOW_UP_MSG

    # ================================================================
    #  通用决策等待
    # ================================================================
    async def _handle_awaiting(self, sid, msg, s, broker):
        aw = s["awaiting"]
        s["awaiting"] = None
        pid = aw["current_plan"]

        intent = await self._llm(
            f"用户正在做一个放松小练习，刚被问「{aw['context']}」。\n"
            f"用户回复：{msg}\n"
            f"判断意图（只输出一个词）：\n"
            f"- switch：明确表示这个方法不适合、想换一个别的方法\n"
            f"- quit：明确表示不想做了、要退出、先不继续\n"
            f"- stay：其余所有情况，包括「好」「继续」「明白了」等肯定或模糊回应——默认继续当前方案")

        if intent == "switch":
            # LLM 从用户反馈推断新的 Q 值，重新匹配方案池
            new_q = await self._llm(
                f"当前方案：{pid}\n"
                f"用户反馈：{msg}\n"
                f"用户的Q1(A急性/B慢性)、Q2(A身体/B脑子)、Q3(A想动/B想静)中哪个变了？\n"
                f"输出格式：Q1=A Q2=B Q3=A（只输出新的Q值，不变的也写上）")
            # 解析新Q值，查匹配表
            q1 = s["q1"]; q2 = s["q2"]; q3 = s["q3"]
            for part in new_q.split():
                if part.startswith("Q1="): q1 = part[3:]
                elif part.startswith("Q2="): q2 = part[3:]
                elif part.startswith("Q3="): q3 = part[3:]
            new_matched = self._match(q1, q2, q3)
            candidates = [m for m in new_matched if m != pid]
            if candidates:
                new_pid = candidates[0]
                s["matched"] = new_matched
                s["plan_idx"] = new_matched.index(new_pid)
                s["step"] = 0; s["phase"] = "executing"
                p = self._get_plan(new_pid)
                if p:
                    await broker.trace("workflow.state_change", sid, phase="presenting", method=p["name"])
                    await broker.trace("workflow.state_change", sid, phase="executing", method=p["steps"][0]["name"])
                    yield p["steps"][0]["text"]
                else:
                    yield "我们试试别的。你先深呼吸一下，准备好了告诉我。"
            else:
                yield "目前没有其他合适的方案了。我们先聊聊天放松一下？"
        elif intent == "quit":
            yield "好的，那先放松聊聊天吧。你现在想说什么都可以。"
        else:
            # 默认继续当前步骤：肯定/模糊回应
            p = self._get_plan(pid)
            if p:
                step = p["steps"][s["step"]]
                if step.get("llm"):
                    resp = await self._llm_long(
                        f"当前方案步骤：{step['name']}。用户说：{msg}\n{step['text']}")
                    yield resp if resp else "好的，我们继续。"
                else:
                    yield f"好的，我们继续。{step['text']}"
            else:
                yield "好的，我们继续。"

    # ================================================================
    #  assessing
    # ================================================================
    async def _assess(self, sid, msg, s, broker):
        if s["skip_qa"]:
            p = self._get_plan(s["skip_qa"])
            if p:
                s["matched"] = [s["skip_qa"]]
                s["phase"] = "executing"
                await broker.trace("workflow.state_change", sid, phase="presenting", method=p["name"])
                yield f"好的，我们直接开始「{p['name']}」吧。"
                step0 = await self._next_step(sid, s, p, broker)
                if step0:
                    yield step0
                return
        # 通用拒识检查：用户明确拒绝 → 退出
        reject_words = ["不想", "不紧张", "不需要", "不用", "不了", "别", "不做", "不练", "不回答", "不想做", "写稿", "忙", "没时间"]
        if any(w in msg for w in reject_words):
            s["phase"] = "closed"
            yield "好呢。"
            return

        q = s["current_q"]
        if q == "q1":
            s["q1"] = await self._llm(
                f"用户说：{msg}\n"
                f"判断用户是在说A(急性/要爆炸/快要爆炸/很亢奋/坐不住/停不下来)还是B(慢性/提不起劲/没动力/不想动/很累/一直这样)。不确定才输出?。只输出A/B/?")
            if s["q1"] == "?":
                s["matched"] = ["sensory_anchor"]; s["phase"] = "presenting"
                yield "没关系，那我推荐「感官锚定法」，快速中断焦虑。开始吧？"
            else:
                s["current_q"] = "q2"
                yield "这种感觉主要是在身体上，还是在脑子里？"
        elif q == "q2":
            s["q2"] = await self._llm(
                f"用户说：{msg}\n"
                f"判断用户是在说A(身体上/心跳快/手抖/身体紧绷)还是B(脑子里/反复想/停不下来/思绪乱)。不确定才输出?。只输出A/B/?")
            if s["q2"] == "?": s["q2"] = "A"
            if s["q1"] == "A":
                self._do_match(s)
                async for c in self._show(s, sid, broker): yield c
            else:
                s["current_q"] = "q3"
                yield "你现在是想让自己动起来，还是想让自己静下来？"
        elif q == "q3":
            s["q3"] = await self._llm(
                f"用户说：{msg}\n"
                f"判断用户是想A(动起来/做事/行动)还是B(静下来/休息/放松)。不确定输出?。只输出A/B/?")
            self._do_match(s)
            async for c in self._show(s, sid, broker): yield c

    def _do_match(self, s):
        s["matched"] = self._match(s["q1"], s["q2"], s["q3"])
        s["plan_idx"] = 0

    async def _show(self, s, sid, broker):
        s["phase"] = "presenting"
        pid = s["matched"][s["plan_idx"]]
        p = self._get_plan(pid)
        await broker.trace("workflow.state_change", sid, phase="presenting", method=p["name"])
        yield await self._llm_long(f"推荐「{p['name']}」：{p['description']}（{p['estimated_duration_minutes']}分钟）。用2-3句话自然介绍，像朋友推荐。80字内。")

    # ================================================================
    #  presenting
    # ================================================================
    async def _presenting(self, sid, msg, s, broker):
        intent = await self._llm(f"用户说：{msg}\n意图：accept/reject/change/other。只输出一个词。")
        if intent == "change":
            s["plan_idx"] += 1
            if s["plan_idx"] < len(s["matched"]):
                async for c in self._show(s, sid, broker): yield c
            else:
                s["phase"] = "closed"
                yield "好的，那我们先不继续了。你现在有什么想法呢？"
        elif intent == "reject":
            s["phase"] = "closed"
            yield "好的，那我们先不继续了，你现在有什么想法呢？"
        elif intent == "accept":
            pid = s["matched"][s["plan_idx"]]; p = self._get_plan(pid)
            s["phase"] = "executing"; s["step"] = 0
            await broker.trace("workflow.state_change", sid, phase="executing", method=p["steps"][0]["name"])
            if p["steps"][0].get("llm"):
                resp = await self._llm_long(
                    f"当前方案步骤：{p['steps'][0]['name']}。用户说：{msg}\n{p['steps'][0]['text']}")
                yield resp if resp else p["steps"][0]["text"]
            else:
                yield p["steps"][0]["text"]
        else: yield "你是想试试看，还是不太适合？"

    # ================================================================
    #  executing
    # ================================================================
    async def _executing(self, sid, msg, s, broker):
        pid = s["matched"][s["plan_idx"]]
        p = self._get_plan(pid)
        step = p['steps'][s['step']]

        total_steps = len(p["steps"])

        if p["id"] == "gratitude_snapshot":
            # 惰性初始化 events
            if "events" not in s:
                s["events"] = []
            intent_raw = await self._llm(
                GRATITUDE_INTENT_PROMPT.format(
                    step_name=step['name'],
                    last_bot=s.get("last_bot_msg", ""),
                    msg=msg))
            raw = _norm_sep(intent_raw.strip())
            await broker.trace("workflow.intent_raw", sid, raw=raw)

            # 解析 LLM 提取的信息类型
            detected = set(x.strip() for x in raw.split(",") if x.strip())

            # 更新结构化事件追踪
            if "event" in detected:
                s["events"].append({"event": msg, "feeling": None, "credit": None})
            if detected & {"feeling", "credit"} and s["events"]:
                cur = s["events"][-1]
                if "feeling" in detected:
                    cur["feeling"] = msg
                if "credit" in detected:
                    cur["credit"] = msg

            # 反思步：单字肯定词（对/是/嗯）不可能是 done
            if s['step'] == 1 and raw in ("done",) and msg.strip() in ("对", "是", "嗯", "对的", "是的", "嗯嗯"):
                raw = "feeling"
                detected = {"feeling"}

            # 代码决策：根据检测到的信息类型决定下一步
            if "more" in detected:
                intent_raw = "done→0"
            elif "done" in detected:
                intent_raw = f"done→{total_steps - 1}"  # 去品味收尾，不跳过
            elif "other" in detected:
                intent_raw = "other"
            elif detected == {"event", "feeling", "credit"}:
                intent_raw = "done→2"  # 三齐，跳过反思
            elif "event" in detected:
                intent_raw = "done→1"  # 有新事件（可能缺感受/功劳），去反思
            elif detected & {"feeling", "credit"}:
                intent_raw = "done→2"  # 补充已有事件，完成
            # 兜底：未识别 → 保持原样（other）
        else:
            steps_list = "\n".join(
                f"  [{i}] {st['name']}" for i, st in enumerate(p["steps"]))
            intent_raw = await self._llm(
                LINEAR_INTENT_PROMPT.format(
                    steps_list=steps_list,
                    s_step=s['step'], step_name=step['name'],
                    last_bot=s.get("last_bot_msg", ""), msg=msg))
            # 线性方案：LLM 只输出完成了哪些步，代码算目标
            raw = intent_raw.strip()
            await broker.trace("workflow.intent_raw", sid, raw=raw)
            # 兼容 LLM 输出「做好了」等价于 current
            if raw in ("做好了", "好了", "继续"):
                raw = "current"
            if raw == "current":
                intent_raw = f"done→{s['step'] + 1}"
            elif raw.startswith("jump:"):
                target_str = _norm_sep(raw.split(":", 1)[1].strip())
                parts = [x.strip() for x in target_str.split(",") if x.strip().isdigit()]
                if len(parts) > 1:
                    # LLM 混淆格式：jump 带了多个数字，当步骤列表处理
                    indices = [int(p) for p in parts]
                    target = self._find_gap(indices)
                    intent_raw = f"done→{min(target, total_steps)}"
                else:
                    target = int(parts[0]) if parts else s['step']
                    intent_raw = f"done→{target}"
            elif raw == "quit":
                intent_raw = f"done→{total_steps}"
            elif raw and raw[0].isdigit():
                indices = [int(x.strip()) for x in _norm_sep(raw).split(",") if x.strip().isdigit()]
                if indices:
                    target = self._find_gap(indices)
                    intent_raw = f"done→{min(target, total_steps)}"
            # 兜底：LLM 没按格式输出，尝试从原文提取数字
            if "done→" not in intent_raw:
                digits_in_raw = [int(x) for x in _norm_sep(raw).split(",") if x.strip().isdigit()]
                if not digits_in_raw:
                    # 逗号分割不行，尝试提取所有独立数字
                    digits_in_raw = [int(m) for m in _DIGITS_RE.findall(raw)]
                if digits_in_raw:
                    target = self._find_gap(digits_in_raw)
                    intent_raw = f"done→{min(target, total_steps)}"
            # else: stuck, worse, failed, other — 保持原样

        intent_word = intent_raw.split("→")[0].strip()

        if intent_word == "stuck":
            yield await self._llm_long(
                f"用户正在执行方案「{p['name']}」，当前步骤：{step['name']} — {step['text']}。\n"
                f"用户卡住了，说：{msg}\n"
                f"请简短帮用户理解这一步要做什么、怎么做（1-2句），然后自然地鼓励用户试试。不要复读步骤原文。")
        elif intent_word == "done":
            digits = "".join(c for c in intent_raw if c.isdigit())
            target = int(digits) if digits else s["step"] + 1
            # 不越界：允许到 total_steps（触发收尾），异常值也由 _advance 兜底
            s["step"] = max(0, min(target, total_steps))
            yield await self._advance(sid, s, p, broker, msg)
            # 最后一步完成后自动进入收尾
            if s["step"] >= total_steps - 1:
                s["phase"] = "following_up"
        elif intent_word in FEEDBACK_PROMPTS:
            s["awaiting"] = {"context": AWAIT_CONTEXT, "current_plan": pid}
            yield await self._llm_long(FEEDBACK_PROMPTS[intent_word].format(
                name=p["name"], step=step["name"], desc=p["description"], msg=msg))
        else:
            s["last_bot_msg"] = step['text']
            yield f"我们继续这一步：{step['text']}"

    @staticmethod
    def _find_gap(indices: list[int]) -> int:
        """从最小已完成步扫描，找第一个缺口。无缺口则返回 max+1。"""
        completed = set(indices)
        target = min(indices)
        while target in completed:
            target += 1
        if target > max(indices):
            target = max(indices) + 1
        return target

    async def _advance(self, sid, s, p, broker, msg=""):
        while s["step"] < len(p["steps"]):
            text = await self._next_step(sid, s, p, broker, msg)
            if text is not None:
                return text
            s["step"] += 1  # SKIP：跳过本步，继续下一个
        return await self._follow_up(s, sid, broker)

    async def _next_step(self, sid, s, p, broker, msg=""):
        step = p['steps'][s['step']]
        await broker.trace("workflow.state_change", sid, phase="executing", method=step['name'])
        if step.get("llm"):
            prompt = f"当前方案步骤：{step['name']}。用户说：{msg}\n"
            # 品味步骤：注入用户分享过的所有内容
            if step['name'] == '品味' and s.get('events'):
                lines = []
                for ev in s['events']:
                    parts = [f"事件：{ev['event']}"]
                    if ev['feeling']: parts.append(f"感受：{ev['feeling']}")
                    if ev['credit']: parts.append(f"功劳：{ev['credit']}")
                    lines.append(" | ".join(parts))
                prompt += "用户本轮分享的感恩事件：\n" + "\n".join(f"- {line}" for line in lines) + "\n\n"
            prompt += step['text']
            resp = await self._llm_long(prompt)
            result = None if resp.strip().rstrip("。，.!；;").upper() == "SKIP" else resp
        else:
            result = step['text']
        if result:
            s["last_bot_msg"] = result
        return result

    async def _follow_up(self, s, sid, broker):
        await broker.trace("workflow.state_change", sid, phase="following_up")
        return FOLLOW_UP_MSG
