// HeartBuddy 前端类型定义 — 与 backend/shared/schemas.py 对齐

// ---- 聊天消息 ----
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

// ---- API 请求/响应 ----
export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface SessionCreateResponse {
  session_id: string;
}

// ---- Trace 事件类型枚举 ----
export type TraceEventType =
  // 会话
  | "session.created"
  | "session.ended"
  // 感知
  | "agent.perceive"
  | "emotion.detected"
  // 思考（DeepSeek R1 推理链）
  | "agent.think.start"
  | "agent.think.chunk"
  | "agent.think.complete"
  // 决策
  | "route.decision"
  | "agent.active"
  // 计划
  | "agent.plan"
  // 行动
  | "agent.action"
  | "llm.request"
  // 观察
  | "agent.observe"
  | "llm.response_complete"
  | "context.loaded"
  | "db.query"
  // 输出
  | "sse.text_complete"
  // 错误
  | "sse.error"
  // 工作流（V1.2）
  | "workflow.state_change"
  | "workflow.intent_raw"
  | "plan.match"
  | "tool.call"
  | "tool.result"
  // 仅日志（不推 WS）
  | "llm.response_chunk"
  | "sse.text_chunk";

// ---- Trace 事件 ----
export interface TraceEvent {
  type: TraceEventType;
  timestamp: string;
  session_id: string;
  data: Record<string, unknown>;
}

// ---- SSE 事件负载 ----
export interface SSETextChunk {
  session_id: string;
  content: string;
}

export interface SSETextComplete {
  session_id: string;
  message_id: number;
  full_text: string;
}

export interface SSEError {
  session_id: string;
  error: string;
  message: string;
}

export type SSEEvent =
  | { event: "sse.text_chunk"; data: SSETextChunk }
  | { event: "sse.text_complete"; data: SSETextComplete }
  | { event: "sse.error"; data: SSEError };

// ---- Trace 阶段分组 ----
export type TracePhase = "perceive" | "think" | "decide" | "plan" | "act" | "observe" | "output" | "judge";

export const TRACE_PHASE_MAP: Record<string, TracePhase> = {
  "agent.perceive": "perceive",
  "emotion.detected": "perceive",
  "agent.think.start": "think",
  "agent.think.chunk": "think",
  "agent.think.complete": "think",
  "route.decision": "decide",
  "agent.active": "decide",
  "agent.plan": "plan",
  "agent.action": "act",
  "llm.request": "act",
  "agent.observe": "observe",
  "llm.response_complete": "observe",
  "context.loaded": "act",
  "db.query": "act",
  "sse.text_complete": "output",
  "sse.error": "output",
};

export const PHASE_LABELS: Record<TracePhase, { label: string; emoji: string; color: string }> = {
  perceive: { label: "感知", emoji: "👁️", color: "#a855f7" },
  think: { label: "思考", emoji: "💭", color: "#e2b714" },
  decide: { label: "决策", emoji: "🧠", color: "#4f8cff" },
  plan: { label: "计划", emoji: "📋", color: "#f59e0b" },
  act: { label: "行动", emoji: "⚡", color: "#f97316" },
  observe: { label: "观察", emoji: "🔍", color: "#10b981" },
  output: { label: "输出", emoji: "✅", color: "#16a34a" },
  judge: { label: "判断", emoji: "🧠", color: "#8b5cf6" },
};

// ---- Trace 类型显示配置 ----
export const TRACE_TYPE_CONFIG: Record<string, { label: string; color: string; emoji: string }> = {
  "session.created": { label: "会话创建", color: "#4ecdc4", emoji: "🟢" },
  "session.ended": { label: "会话结束", color: "#ff6b6b", emoji: "🔴" },
  "agent.perceive": { label: "感知", color: "#a855f7", emoji: "👁️" },
  "emotion.detected": { label: "情绪检测", color: "#a855f7", emoji: "🎭" },
  "agent.think.start": { label: "开始思考", color: "#e2b714", emoji: "💭" },
  "agent.think.chunk": { label: "思考中", color: "#c9a30e", emoji: "···" },
  "agent.think.complete": { label: "思考完成", color: "#e2b714", emoji: "💡" },
  "route.decision": { label: "路由决策", color: "#4f8cff", emoji: "🔀" },
  "agent.active": { label: "Agent 激活", color: "#06b6d4", emoji: "🤖" },
  "agent.plan": { label: "计划", color: "#f59e0b", emoji: "📋" },
  "agent.action": { label: "行动", color: "#f97316", emoji: "⚡" },
  "agent.observe": { label: "观察", color: "#10b981", emoji: "🔍" },
  "db.query": { label: "数据库查询", color: "#94a3b8", emoji: "🗄️" },
  "llm.request": { label: "LLM 请求", color: "#6366f1", emoji: "📤" },
  "llm.response_complete": { label: "LLM 完成", color: "#3b82f6", emoji: "✨" },
  "context.loaded": { label: "上下文加载", color: "#94a3b8", emoji: "📚" },
  "sse.text_complete": { label: "最终输出", color: "#16a34a", emoji: "✅" },
  "sse.error": { label: "错误", color: "#dc2626", emoji: "❌" },
  "workflow.state_change": "act",
  "workflow.intent_raw": "judge",
  "plan.match": "plan",
  "tool.call": { label: "工具调用", color: "#f97316", emoji: "🔧" },
  "tool.result": { label: "工具结果", color: "#84cc16", emoji: "✅" },
  "sse.text_chunk": { label: "文本片段", color: "#ccc", emoji: "💬" },
  "llm.response_chunk": { label: "Token", color: "#ccc", emoji: "📥" },
};
