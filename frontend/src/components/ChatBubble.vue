<script setup lang="ts">
import { computed } from "vue";
import type { ChatMessage } from "../types";

const props = defineProps<{
  message: ChatMessage;
  isStreaming?: boolean;
}>();

const time = computed(() => {
  if (props.message.timestamp) return props.message.timestamp;
  const now = new Date();
  return now.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
});
</script>

<template>
  <div
    class="chat-bubble"
    :class="{
      'chat-bubble--user': message.role === 'user',
      'chat-bubble--assistant': message.role === 'assistant',
      'chat-bubble--streaming': isStreaming,
    }"
  >
    <div v-if="message.role === 'assistant'" class="chat-bubble__avatar">💛</div>
    <div class="chat-bubble__body">
      <div class="chat-bubble__content">
        <p class="chat-bubble__text">{{ message.content }}</p>
        <span v-if="isStreaming" class="chat-bubble__typing-indicator">●</span>
      </div>
      <span class="chat-bubble__time">{{ time }}</span>
    </div>
  </div>
</template>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 8px;
  padding: 4px 0;
}

.chat-bubble--user {
  flex-direction: row-reverse;
}

.chat-bubble__avatar {
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

.chat-bubble__content {
  padding: 10px 14px;
  border-radius: 16px;
  line-height: 1.5;
  word-break: break-word;
  width: fit-content;
}

.chat-bubble--assistant .chat-bubble__content {
  max-width: 100%;
  background: rgba(209, 250, 229, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  color: #1a1a2e;
  border-top-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-bubble--user .chat-bubble__content {
  max-width: calc(100% - 40px);
  background: rgba(233, 213, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  color: #1a1a2e;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-bubble__text {
  margin: 0;
  font-size: 14px;
  white-space: pre-wrap;
}

.chat-bubble__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chat-bubble--user .chat-bubble__body {
  align-items: flex-end;
}

.chat-bubble__time {
  font-size: 10px;
  color: rgba(0, 0, 0, 0.45);
  padding: 0 4px;
}

.chat-bubble__typing-indicator {
  display: inline-block;
  margin-left: 4px;
  animation: blink 0.8s infinite;
  color: var(--color-primary);
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.2;
  }
}
</style>
