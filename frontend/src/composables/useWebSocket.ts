/**
 * useWebSocket — WebSocket 连接管理，接收 trace 事件
 *
 * 功能：
 * - 自动连接 /ws/monitor
 * - 断线自动重连（固定 3 秒间隔）
 * - 保留最近 N 条 trace
 */

import { ref, onUnmounted, type Ref } from "vue";
import type { TraceEvent, TraceEventType } from "../types";

const MAX_TRACES = 200;

export function useWebSocket() {
  const traces = ref<TraceEvent[]>([]);
  const isConnected = ref(false);
  const activeTypes = ref<Set<TraceEventType>>(new Set());

  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let shouldReconnect = true;

  function connect() {
    shouldReconnect = true;

    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${location.host}/ws/monitor`;

    try {
      ws = new WebSocket(url);

      ws.onopen = () => {
        isConnected.value = true;
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const trace: TraceEvent = JSON.parse(event.data as string);
          if (traces.value.length >= MAX_TRACES) {
            traces.value.splice(0, traces.value.length - MAX_TRACES + 1);
          }
          traces.value.push(trace);
        } catch {
          // 忽略解析失败的消息
        }
      };

      ws.onclose = () => {
        isConnected.value = false;
        ws = null;

        if (shouldReconnect) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        // onclose 会紧随其后触发，在 onclose 中处理重连
      };
    } catch {
      // 连接失败，稍后重连
      if (shouldReconnect) {
        reconnectTimer = setTimeout(connect, 3000);
      }
    }
  }

  function disconnect() {
    shouldReconnect = false;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    ws?.close();
    ws = null;
    isConnected.value = false;
  }

  function clearTraces() {
    traces.value = [];
  }

  function toggleType(type: TraceEventType) {
    const next = new Set(activeTypes.value);
    if (next.has(type)) {
      next.delete(type);
    } else {
      next.add(type);
    }
    activeTypes.value = next;
  }

  function clearFilter() {
    activeTypes.value = new Set();
  }

  return {
    traces,
    isConnected,
    activeTypes,
    connect,
    disconnect,
    clearTraces,
    toggleType,
    clearFilter,
  };
}
