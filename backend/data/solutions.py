"""方案库 — 缓解紧张的 5 个结构化方案（硬编码，V1.2 使用）

方案配置文件格式（V1.2 可从 JSON/YAML 热加载）：
    {
        "id": "unique_id",
        "name": "方案名称",
        "description": "一句话介绍",
        "suitable_emotions": ["anxious", "stressed"],
        "estimated_duration_minutes": 5,
        "steps": ["步骤1", "步骤2", ...],
    }
"""

SOLUTIONS: list[dict] = [
    {
        "id": "sensory_anchor",
        "name": "感官锚定法",
        "description": "通过五感观察将注意力从情绪脑转移到感知皮层，快速中断焦虑循环。",
        "suitable_emotions": ["anxious", "panicked", "stressed"],
        "estimated_duration_minutes": 3,
        "steps": [
            "暂停：先做一个深深的呼吸，准备好了告诉我。",
            "看：环顾四周，寻找并告诉我5个你看到的东西。",
            "触摸：触摸并告诉我4个你能感受其质感的东西。",
            "听：静下心来，告诉我你听到的3个声音。",
            "闻：告诉我你闻到的2个气味。",
            "尝：吃一口什么，或回忆你喜欢的食物是什么味道的。",
        ],
    },
    {
        "id": "emotion_naming",
        "name": "情绪命名与抽屉法",
        "description": "将模糊的情绪感受转化为具体的词语，并想象放进抽屉，获得控制感。",
        "suitable_emotions": ["anxious", "overwhelmed", "ruminating"],
        "estimated_duration_minutes": 5,
        "steps": [
            "识别：现在你感受到的情绪有哪些？试着用具体的词描述（不只是紧张，也许是'对不确定性的恐惧'）。",
            "定位：这些情绪在你身体的哪个位置？",
            "命名抽屉：给每种情绪起一个名字，想象把它放进一个标有名字的抽屉里。",
            "关上抽屉：深呼吸，想象轻轻关上每个抽屉。它们还在，但你现在可以选择什么时候打开。",
        ],
    },
    {
        "id": "progressive_relaxation",
        "name": "渐进式肌肉放松",
        "description": "通过依次收紧再放松身体各肌群，释放躯体紧张。",
        "suitable_emotions": ["anxious", "stressed", "tense"],
        "estimated_duration_minutes": 10,
        "steps": [
            "准备：找个舒服的姿势坐好或躺好，闭上眼睛。",
            "脚部：用力绷紧脚趾和脚掌5秒……然后突然放松，感受松弛感。",
            "小腿和大腿：收紧腿部肌肉5秒……放松。",
            "腹部：收紧腹肌5秒……放松。",
            "手臂和手：握紧拳头，收紧手臂5秒……放松。",
            "肩颈：耸起肩膀靠近耳朵5秒……放松。",
            "面部：皱紧整张脸5秒……放松。",
            "全身：感受从头到脚的放松感，深呼吸3次。",
        ],
    },
    {
        "id": "gratitude_snapshot",
        "name": "感恩速记",
        "description": "快速记录当天值得感恩的微小事物，切换注意力焦点。",
        "suitable_emotions": ["sad", "low_energy", "ruminating"],
        "estimated_duration_minutes": 6,
        "steps": [
            "回忆：想想今天发生的，哪怕再微不足道的好事。",
            "记录3件：告诉我今天让你感到温暖、开心或感激的3件小事。",
            "品味：选其中一件，详细描述它发生时的场景和你的感受。",
            "收尾：感受一下此刻的情绪变化。",
        ],
    },
    {
        "id": "micro_victory",
        "name": "微型胜利法",
        "description": "通过完成一个极小的行动任务，打破'什么都做不了'的无力感循环。",
        "suitable_emotions": ["low_energy", "stuck", "overwhelmed"],
        "estimated_duration_minutes": 1,
        "steps": [
            "选择：从以下选一个你现在就能做的微小行动：站起来伸个懒腰 / 喝一杯水 / 把桌面上的一样东西归位 / 写下此刻脑海中的一个念头。",
            "执行：现在就去完成它，完成后告诉我。",
            "庆祝：完成了！给自己一个认可——哪怕只是对自己说'我做到了'。",
            "扩展（可选）：要不要再来一个？还是现在感觉好些了？",
        ],
    },
]
