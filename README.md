# HeartBuddy · 心灵伙伴

AI 情感陪伴机器人 — MVP V1.2 工作流闭环。

一个能陪用户闲聊、执行结构化放松方案、实时监控 AI 决策链的 Web 聊天工具。

## 技术栈

| 层 | 选型 |
|---|------|
| 前端 | Vue 3 + Vite + TypeScript |
| 后端 | Python 3.11+ / FastAPI |
| 数据库 | SQLite |
| LLM | DeepSeek API |
| 实时通信 | SSE（聊天流）+ WebSocket（监控 trace） |

## 快速启动

### 前置条件

- Node.js ≥ 18
- Python ≥ 3.11
- DeepSeek API Key（[获取](https://platform.deepseek.com/api_keys)）

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
cd ..
PYTHONPATH=. uvicorn backend.main:app --reload --port 8000
```

后端启动后访问：
- `http://localhost:8000/api/health` — 健康检查
- `http://localhost:8000/docs` — Swagger API 文档

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。

## 项目结构

```
HeartBuddy MVP/
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置中心（.env → Settings）
│   ├── requirements.txt
│   ├── harness/                 # 编排层
│   │   ├── orchestrator.py      # ChatOrchestrator — 全流程编排
│   │   ├── trace_broker.py      # TraceBroker — SSE/WS 双路分发
│   │   ├── router.py            # RouteEngine — 路由决策
│   │   ├── context.py           # ContextManager — 上下文管理
│   │   └── session.py           # SessionManager — 会话管理
│   ├── agents/                  # Agent 执行层
│   │   ├── base.py              # BaseAgent (ABC)
│   │   ├── companion.py         # CompanionAgent — 闲聊共情
│   │   └── workflow.py          # WorkflowAgent — 5 方案完整状态机 (V1.2)
│   ├── data/                    # 数据层
│   │   ├── db.py + repository.py
│   │   └── solutions.py         # 5 个缓解紧张方案（V1.2 使用）
│   ├── services/                # 外部服务
│   │   ├── llm_client.py        # DeepSeek API
│   │   ├── emotion_detector.py  # 情绪检测（LLM + 关键词降级）
│   │   ├── skill_manager.py     # Skills 管理器
│   │   └── logger.py            # JSON Lines 日志
│   ├── api/                     # 端点
│   │   ├── chat.py              # POST /api/chat (SSE)
│   │   └── monitor.py           # WS /ws/monitor
│   └── shared/schemas.py        # Pydantic 数据模型
├── skills/                      # 知识技能文件
│   ├── soul.md                  # 核心人格
│   └── emotion-guide.md         # 情绪应对策略
├── frontend/
│   └── src/
│       ├── App.vue              # 双栏布局
│       ├── components/
│       │   ├── PhoneSimulator.vue   # 手机模拟器（左栏）
│       │   ├── ChatMessageList.vue  # 消息列表
│       │   ├── ChatBubble.vue       # 聊天气泡
│       │   ├── ChatInput.vue        # 输入框
│       │   └── MonitorConsole.vue   # 监控面板（右栏）
│       ├── composables/
│       │   ├── useSSE.ts / useWebSocket.ts / useChat.ts
│       └── types/index.ts          # TS 类型定义
├── .env.example
└── README.md
```

## 核心架构

### 双路分发 (TraceBroker)

```
用户消息 → ChatOrchestrator → Agent.process()
                │
                ├─ SSE → 手机模拟器（只推送 text_chunk / text_complete / error）
                └─ WebSocket → 监控面板（推送全部 trace 事件）
```

### Trace 事件类型

| 类型 | 说明 | V1.1 状态 |
|------|------|----------|
| `session.created/ended` | 会话生命周期 | ✅ 完整 |
| `route.decision` | 路由决策 | ✅ 固定 companion |
| `emotion.detected` | 情绪检测 | ✅ 关键词，不参与路由 |
| `agent.active` | Agent 激活 | ✅ 完整 |
| `llm.request/response_chunk/response_complete` | LLM 交互全记录 | ✅ 完整 |
| `context.loaded` | 上下文加载 | ✅ 完整 |
| `sse.text_chunk/text_complete/error` | SSE 分发镜像 | ✅ 完整 |
| `workflow.state_change` | 工作流状态机 | ✅ 完整 |
| `workflow.intent_raw` | Agent判断原始输出 | ✅ 完整 |
| `route.decision` | 路由决策 (LLM意图) | ✅ 完整 |
| `plan.match` | 方案匹配 | ✅ 完整 |
| `tool.call/result` | 工具调用 | 🔜 V1.3 |

## V1.2 新增功能

- **WorkflowAgent**：完整状态机（进入→信息采集→方案呈现→逐步执行→出口过渡→结束），5 套结构化方案
  - 感官锚定法（6步）：五感观察，中断焦虑循环
  - 情绪命名与抽屉法（4步）：情绪具象化，获得控制感
  - 渐进式肌肉放松（8步）：依次收紧放松各肌群
  - 感恩速记（4步，可循环）：记录感恩小事，切换注意力焦点
  - 微型胜利法（3步）：极小行动打破无力感
- **LLM 情绪 + 意图检测**：同时输出 emotion/action/method，router 按意图自动路由到 workflow
- **意图检测重构**：感恩速记用语义提取（event/feeling/credit/done/more），线性方案用结构化输出（jump/current/quit/步骤序号）
- **结构化事件追踪**：感恩速记按事件独立追踪感受和功劳，品味步生成个性化总结
- **退出机制**：全局拒识（不想/不需要等），Q&A 任意阶段可退出
- **智能步骤推进**：线性方案支持缺口查找（1,3,5→补4）、枚举步骤数量判断、中文顿号兼容
- **控制台增强**：新增「判断」阶段（紫色），显示 LLM 意图检测原始输出

## V1.1 新增功能

- **LLM 情绪识别**：deepseek-chat 分类 + 关键词降级兜底，支持 anxious/sad/angry/happy/neutral
- **Skills 系统**：skills/ 目录丢 .md 即可扩展，YAML frontmatter 声明，按情绪自动加载
- **动态人设**：SOUL.md（核心人格）+ emotion-guide.md（情绪策略）按需注入 Prompt
- **自然引导**：emotion-guide 内置引导策略，Agent 自主决定是否提议情绪急救工具

## V1.0 → V1.1 → V1.2 扩展路径

| 扩展点 | V1.0 | V1.1 | V1.2 |
|--------|------|------|------|
| `RouteEngine.decide()` | 固定 companion | 情绪 + 引导决策 | 完整上下文路由 |
| `CompanionAgent` | 基础共情 + 关键词情绪 | LLM 情绪识别 + Skills 动态人设 | 长期记忆人设 |
| `WorkflowAgent` | 占位 | —（已移除） | 完整状态机 + 5 方案 |
| `emotion.detected` | 关键词记录 | LLM 识别参与路由 | 细粒度情绪 |
| Skills 系统 | — | skills/ 目录 + 按情绪加载 | 自主选择 + 更多技能 |
| 会话 | 单表 SQLite | 单表 SQLite | 增加 user 表 |

## API 概要

### `POST /api/sessions`
创建会话，返回 `{ session_id }`。

### `POST /api/chat`
发送消息，SSE 流式返回 AI 回复。

请求：`{ "session_id": "...", "message": "..." }`

SSE 事件：
```
event: sse.text_chunk     data: {"session_id":"...","content":"..."}
event: sse.text_complete  data: {"session_id":"...","message_id":42,"full_text":"..."}
event: sse.error          data: {"session_id":"...","error":"...","message":"..."}
```

### `WS /ws/monitor`
WebSocket 实时推送 `TraceEvent` JSON。

### `GET /api/health`
健康检查。

## 开发版本

| 版本 | 内容 | 状态 |
|------|------|------|
| V1.0 | 基础框架：Web 前端 + 后端 API + LLM 接入 + 监控台 | ✅ 完成 |
| V1.1 | 自主Agent：人设 + 闲聊 + 情绪识别 + 自然引导逻辑 | ✅ 完成 |
| V1.2 | 工作流Agent：5方案闭环 + 意图检测重构 + 路由引擎 | ✅ 当前 |
| V1.3 | 枚举步骤数量判断 + Prompt拆分 + 长期记忆 | 🔜 |
