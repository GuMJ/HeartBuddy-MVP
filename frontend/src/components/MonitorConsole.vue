<script setup lang="ts">
/**
 * MonitorConsole — Cursor 终端风格 Agent 决策链
 *
 * 文字流展示，彩色圆点标识阶段，无卡片无边距无 emoji。
 */
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from "vue";
import type { TraceEvent, TraceEventType } from "../types";
import { TRACE_PHASE_MAP, type TracePhase } from "../types";
import { useWebSocket } from "../composables/useWebSocket";

const {
  traces,
  isConnected,
  activeTypes,
  connect,
  disconnect,
  clearTraces,
  toggleType,
  clearFilter,
} = useWebSocket();

onMounted(() => connect());
onUnmounted(() => disconnect());

// ---- 阶段颜色（小圆点） ----
const PHASE_COLORS: Record<TracePhase, string> = {
  perceive: "#a855f7",
  think: "#e2b714",
  decide: "#4f8cff",
  plan: "#f59e0b",
  act: "#f97316",
  observe: "#10b981",
  output: "#16a34a",
};

// ---- 事件 → 可读标签 ----
const TYPE_LABELS: Record<string, string> = {
  "agent.perceive": "感知",
  "emotion.detected": "情绪",
  "agent.think.start": "思考",
  "agent.think.chunk": "",
  "agent.think.complete": "思考完成",
  "route.decision": "路由",
  "agent.active": "激活",
  "agent.plan": "计划",
  "agent.action": "行动",
  "llm.request": "LLM",
  "agent.observe": "结果",
  "llm.response_complete": "LLM完成",
  "context.loaded": "上下文",
  "db.query": "查询",
  "sse.text_complete": "输出",
  "sse.error": "错误",
  "session.created": "会话",
  "session.ended": "结束",
};

// ---- 筛选 ----
const filteredTraces = computed<TraceEvent[]>(() => {
  if (activeTypes.value.size === 0) return traces.value;
  return traces.value.filter((t) => activeTypes.value.has(t.type));
});

// 可选筛选的阶段类型
const FILTER_PHASES: TracePhase[] = ["perceive", "think", "decide", "plan", "act", "observe", "output"];

function isPhaseActive(phase: TracePhase): boolean {
  const types = Object.entries(TRACE_PHASE_MAP)
    .filter(([, p]) => p === phase)
    .map(([t]) => t as TraceEventType);
  if (activeTypes.value.size === 0) return true;
  return types.some((t) => activeTypes.value.has(t));
}

function togglePhase(phase: TracePhase) {
  const types = Object.entries(TRACE_PHASE_MAP)
    .filter(([, p]) => p === phase)
    .map(([t]) => t as TraceEventType);
  const allActive = types.every((t) => activeTypes.value.has(t));
  if (allActive) {
    types.forEach((t) => toggleType(t));
  } else {
    types.forEach((t) => {
      if (!activeTypes.value.has(t)) toggleType(t);
    });
  }
}

// ---- 轮次分组 ----
interface LineItem {
  type: "divider" | "trace" | "think";
  content?: string;
  trace?: TraceEvent;
}

const displayLines = computed<LineItem[]>(() => {
  const lines: LineItem[] = [];
  let turnIndex = 0;

  for (const t of filteredTraces.value) {
    if (t.type === "agent.perceive") {
      turnIndex++;
      const msg = (t.data.user_message as string) || "";
      lines.push({ type: "divider", content: `#${turnIndex}  ${msg}` });
    }

    // 思考块缩进渲染
    if (t.type === "agent.think.chunk") {
      lines.push({ type: "think", content: (t.data.content as string) || "" });
      continue;
    }

    lines.push({ type: "trace", trace: t });
  }
  return lines;
});

// ---- 摘要生成 ----
function formatSummary(trace: TraceEvent): string {
  const d = trace.data;
  switch (trace.type) {
    case "agent.perceive":
      return d.emotion !== "neutral"
        ? `${d.emotion}  ${d.evidence}`
        : "情绪平静";
    case "emotion.detected":
      return `${d.emotion}  conf=${d.confidence}`;
    case "route.decision":
      return `${d.selected_agent}  ${d.reason}`;
    case "agent.active":
      return `${d.agent_name}  ${d.reason}`;
    case "agent.plan":
      return (d.approach as string) || "";
    case "agent.action":
      return (d.detail as string) || "";
    case "llm.request":
      return `${d.model}  ${(d.messages as unknown[])?.length ?? 0}条消息`;
    case "agent.observe":
      return (d.summary as string) || "";
    case "llm.response_complete":
      return `${d.total_chunks}chunks  ${d.duration_ms}ms  ${d.finish_reason}`;
    case "context.loaded":
      return `${d.message_count}条  ~${d.total_tokens_estimate}tokens`;
    case "db.query":
      return `${d.query_type}  ${d.result_count}条`;
    case "agent.think.start":
      return "深度思考…";
    case "agent.think.complete":
      return `${d.total_chunks}步  ${d.duration_ms}ms`;
    case "sse.text_complete":
      return (d.full_text as string)?.slice(0, 100) || "";
    case "sse.error":
      return `${d.error}: ${d.message}`;
    case "session.created":
      return "会话开始";
    case "session.ended":
      return `持续 ${(d.duration_seconds as number)?.toFixed(0)}s`;
    default:
      return JSON.stringify(d).slice(0, 60);
  }
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

// ---- 自动滚动 ----
const listRef = ref<HTMLElement | null>(null);
watch(() => displayLines.value.length, async () => {
  await nextTick();
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight;
  }
});
</script>

<template>
  <div class="monitor">
    <!-- 头部 -->
    <div class="monitor__head">
      <span class="monitor__title">Agent Trace</span>
      <span class="monitor__stat">{{ traces.length }}</span>
      <span class="monitor__spacer" />
      <button
        v-for="p in FILTER_PHASES"
        :key="p"
        class="monitor__filter-dot"
        :class="{ off: !isPhaseActive(p) }"
        :style="{ '--c': PHASE_COLORS[p] }"
        :title="p"
        @click="togglePhase(p)"
      />
    </div>

    <!-- 文字流 -->
    <div ref="listRef" class="monitor__body">
      <div v-if="displayLines.length === 0" class="monitor__empty">
        {{ isConnected ? "等待消息…" : "WebSocket 重连中…" }}
      </div>

      <template v-for="(line, i) in displayLines" :key="i">
        <!-- 分隔线 -->
        <div v-if="line.type === 'divider'" class="monitor__divider">
          <span class="monitor__divider-char">▸</span>
          {{ line.content }}
        </div>

        <!-- 思考行（缩进） -->
        <div v-else-if="line.type === 'think'" class="monitor__think-line">
          <span class="monitor__think-bar" />
          {{ line.content }}
        </div>

        <!-- trace 行 -->
        <div
          v-else-if="line.trace"
          class="monitor__line"
          :class="{ error: line.trace.type === 'sse.error' }"
        >
          <span
            class="monitor__phase-dot"
            :style="{
              background: PHASE_COLORS[TRACE_PHASE_MAP[line.trace.type] ?? 'observe'] ?? '#666',
            }"
          />
          <span class="monitor__label">
            {{ TYPE_LABELS[line.trace.type] || line.trace.type }}
          </span>
          <span class="monitor__time">{{ formatTime(line.trace.timestamp) }}</span>
          <span class="monitor__summary">{{ formatSummary(line.trace) }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.monitor {
  width: 100%;
  height: 700px;
  display: flex;
  flex-direction: column;
  background: rgba(245, 245, 247, 0.7);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  color: #1a1a2e;
  font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  line-height: 1.65;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(0, 0, 0, 0.03);
}

/* ---- 头部 ---- */
.monitor__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  background: transparent;
}

.monitor__title {
  font-weight: 600;
  font-size: 12px;
  color: #6b6b6b;
  letter-spacing: 0.5px;
}

.monitor__stat {
  font-size: 10px;
  color: #8b8b8b;
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 8px;
}

.monitor__spacer {
  flex: 1;
}

.monitor__filter-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--c);
  border: none;
  cursor: pointer;
  opacity: 1;
  transition: opacity 0.15s;
}
.monitor__filter-dot.off {
  opacity: 0.2;
}

/* ---- 主体 ---- */
.monitor__body {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0 20px;
}

.monitor__empty {
  padding: 40px 20px;
  text-align: center;
  color: #8b8b8b;
}

/* ---- 分隔线 ---- */
.monitor__divider {
  padding: 12px 14px 6px;
  color: #58a6ff;
  font-weight: 600;
  font-size: 12px;
  box-shadow: 0 -1px 0 rgba(0, 0, 0, 0.04);
  margin-top: 2px;
}
.monitor__divider:first-child {
  border-top: none;
  margin-top: 0;
}
.monitor__divider-char {
  margin-right: 6px;
}

/* ---- trace 行 ---- */
.monitor__line {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 2px 14px;
  flex-wrap: wrap;
}

.monitor__summary {
  color: #1a1a2e;
  word-break: break-word;
  flex: 1;
  min-width: 0;
}
.monitor__line.error {
  color: #f85149;
}

.monitor__phase-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.monitor__label {
  color: #6b6b6b;
  font-size: 11px;
  flex-shrink: 0;
  min-width: 42px;
}

.monitor__time {
  color: #8b8b8b;
  font-size: 10px;
  flex-shrink: 0;
  min-width: 64px;
}


/* ---- 思考行（缩进） ---- */
.monitor__think-line {
  color: #6b6b6b;
  font-size: 11px;
  line-height: 1.7;
  padding: 1px 14px 1px 56px;
  display: flex;
  align-items: baseline;
  gap: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}

.monitor__think-bar {
  flex-shrink: 0;
  width: 1px;
  height: 1em;
  background: #e2b71433;
}
</style>
