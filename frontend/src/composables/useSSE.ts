/**
 * useSSE — 通过 fetch + ReadableStream 解析 SSE 流
 *
 * EventSource 不支持 POST，因此使用 fetch API 手动解析。
 */

import { ref, type Ref } from "vue";
import type { SSEEvent } from "../types";

export interface SSECallbacks {
  onTextChunk: (content: string) => void;
  onTextComplete: (fullText: string) => void;
  onError: (error: string) => void;
}

export function useSSE() {
  const isStreaming = ref(false);
  let abortController: AbortController | null = null;

  async function connect(
    sessionId: string,
    message: string,
    callbacks: SSECallbacks
  ): Promise<void> {
    // 取消之前的请求
    disconnect();

    abortController = new AbortController();
    isStreaming.value = true;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errText = await response.text();
        callbacks.onError(`HTTP ${response.status}: ${errText}`);
        isStreaming.value = false;
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError("无法读取响应流");
        isStreaming.value = false;
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 解析 SSE 事件（按 \n\n 分割）
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || ""; // 最后一个不完整块保留

        for (const part of parts) {
          const trimmed = part.trim();
          if (!trimmed) continue;

          const parsed = parseSSEEvent(trimmed);
          if (!parsed) continue;

          switch (parsed.event) {
            case "sse.text_chunk":
              callbacks.onTextChunk(parsed.data.content);
              break;
            case "sse.text_complete":
              callbacks.onTextComplete(parsed.data.full_text);
              break;
            case "sse.error":
              callbacks.onError(parsed.data.message);
              break;
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // 被用户取消，不报错
      } else {
        callbacks.onError(err instanceof Error ? err.message : "网络请求失败");
      }
    } finally {
      isStreaming.value = false;
      abortController = null;
    }
  }

  function disconnect() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    isStreaming.value = false;
  }

  return { isStreaming, connect, disconnect };
}

/**
 * 解析单条 SSE 事件字符串
 * 格式：event: <type>\ndata: <json>
 */
function parseSSEEvent(raw: string): SSEEvent | null {
  const lines = raw.split("\n");
  let eventType = "";
  let dataJson = "";

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      eventType = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      dataJson = line.slice(6).trim();
    }
  }

  if (!eventType || !dataJson) return null;

  try {
    const data = JSON.parse(dataJson);
    return { event: eventType as SSEEvent["event"], data };
  } catch {
    return null;
  }
}
