/**
 * useChat — 聊天状态管理
 *
 * 管理消息列表、发送消息、SSE 流式接收。
 */

import { ref, type Ref } from "vue";
import { useSSE } from "./useSSE";
import type { ChatMessage } from "../types";

export function useChat(sessionId: Ref<string>) {
  const messages = ref<ChatMessage[]>([]);
  const isLoading = ref(false);
  const currentStreaming = ref("");
  const currentEmotion = ref("neutral");
  const error = ref("");

  const { isStreaming, connect: connectSSE, disconnect } = useSSE();

  async function send(text: string, entry: string = "chat"): Promise<void> {
    if (!text.trim() || isLoading.value) return;

    messages.value.push({ role: "user", content: text });
    error.value = "";
    isLoading.value = true;
    currentStreaming.value = "";

    await connectSSE(sessionId.value, text, entry, {
      onTextChunk(chunk: string) {
        currentStreaming.value += chunk;
      },
      onTextComplete(fullText: string, extra?: Record<string, unknown>) {
        messages.value.push({ role: "assistant", content: fullText });
        currentStreaming.value = "";
        isLoading.value = false;
        if (extra?.emotion) {
          currentEmotion.value = extra.emotion as string;
        }
      },
      onError(err: string) {
        error.value = err;
        isLoading.value = false;
        currentStreaming.value = "";
      },
    });
  }

  function clearMessages() {
    messages.value = [];
    currentStreaming.value = "";
    currentEmotion.value = "neutral";
    error.value = "";
    isLoading.value = false;
  }

  return {
    messages,
    isLoading,
    currentStreaming,
    currentEmotion,
    error,
    send,
    clearMessages,
    disconnect,
  };
}
