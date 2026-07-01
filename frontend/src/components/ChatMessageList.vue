<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import type { ChatMessage } from "../types";
import ChatBubble from "./ChatBubble.vue";

const props = defineProps<{
  messages: ChatMessage[];
  currentStreaming: string;
  isLoading: boolean;
}>();

const listRef = ref<HTMLElement | null>(null);

// 自动滚动到底部
async function scrollToBottom() {
  await nextTick();
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight;
  }
}

watch(
  [() => props.messages.length, () => props.currentStreaming],
  () => scrollToBottom(),
);
</script>

<template>
  <div ref="listRef" class="message-list">
    <!-- 空状态 -->
    <div v-if="messages.length === 0 && !isLoading" class="message-list__empty">
      <div class="message-list__empty-icon">💛</div>
      <p class="message-list__empty-title">Hi，我是 HeartBuddy</p>
      <p class="message-list__empty-subtitle">你的 AI 情感陪伴伙伴，有什么想聊的？</p>
    </div>

    <!-- 消息列表 -->
    <ChatBubble
      v-for="(msg, index) in messages"
      :key="index"
      :message="msg"
    />

    <!-- 流式回复（未完成） -->
    <div v-if="isLoading && currentStreaming" class="streaming-message">
      <div class="chat-bubble__avatar-streaming">💛</div>
      <div class="chat-bubble__content-streaming">
        <p>{{ currentStreaming }}</p>
        <span class="chat-bubble__typing-indicator">●</span>
      </div>
    </div>

    <!-- 等待加载（已发送但尚未收到第一个 chunk） -->
    <div v-if="isLoading && !currentStreaming" class="streaming-message">
      <div class="chat-bubble__avatar-streaming">💛</div>
      <div class="chat-bubble__content-streaming thinking">
        <span class="dot-1">●</span>
        <span class="dot-2">●</span>
        <span class="dot-3">●</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-list__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-secondary);
  text-align: center;
  padding: 40px 20px;
}

.message-list__empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.message-list__empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.message-list__empty-subtitle {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.5);
}

/* 流式消息 */
.streaming-message {
  display: flex;
  gap: 8px;
  padding: 4px 0;
}

.chat-bubble__avatar-streaming {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.5);
}

.chat-bubble__content-streaming {
  max-width: 100%;
  width: fit-content;
  padding: 10px 14px;
  border-radius: 16px;
  border-top-left-radius: 4px;
  background: rgba(209, 250, 229, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  font-size: 14px;
  color: #1a1a2e;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-bubble__content-streaming p {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-bubble__content-streaming.thinking {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 16px 14px;
}

.thinking span {
  font-size: 8px;
  animation: bounce 1.2s infinite;
}

.thinking .dot-1 { animation-delay: 0s; }
.thinking .dot-2 { animation-delay: 0.2s; }
.thinking .dot-3 { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { opacity: 0.2; transform: translateY(0); }
  40% { opacity: 1; transform: translateY(-4px); }
}

.chat-bubble__typing-indicator {
  display: inline-block;
  margin-left: 4px;
  animation: blink 0.8s infinite;
  color: var(--color-primary);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}
</style>
