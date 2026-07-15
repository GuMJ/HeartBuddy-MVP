<script setup lang="ts">
/**
 * PhoneSimulator — 手机模拟器，封装聊天界面
 *
 * 左侧面板主组件，集成消息列表 + 输入框 + SSE 连接。
 */
import type { ChatMessage } from "../types";
import ChatMessageList from "./ChatMessageList.vue";
import ChatInput from "./ChatInput.vue";

defineProps<{
  messages: ChatMessage[];
  currentStreaming: string;
  isLoading: boolean;
  error: string;
}>();

const emit = defineEmits<{
  send: [text: string, entry?: string];
}>();
</script>

<template>
  <div class="phone-simulator">
    <!-- 状态栏 -->
    <div class="phone-statusbar">
      <span class="phone-statusbar__time">9:41</span>
      <div class="phone-statusbar__icons">
        <svg width="15" height="11" viewBox="0 0 15 11">
          <rect x="0" y="8" width="3" height="3" rx="0.7" fill="currentColor"/>
          <rect x="4" y="5" width="3" height="6" rx="0.7" fill="currentColor"/>
          <rect x="8" y="2.5" width="3" height="8.5" rx="0.7" fill="currentColor"/>
          <rect x="12" y="0" width="3" height="11" rx="0.7" fill="currentColor" opacity="0.35"/>
        </svg>
        <span class="phone-statusbar__5g">5G</span>
        <svg width="25" height="12" viewBox="0 0 25 12">
          <rect x="0.5" y="0.5" width="20" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5"/>
          <rect x="2" y="2" width="17" height="8" rx="1.5" fill="currentColor"/>
          <rect x="22" y="3.5" width="2.5" height="5" rx="1.2" fill="currentColor" opacity="0.35"/>
        </svg>
      </div>
    </div>

    <!-- 聊天头部 -->
    <div class="phone-header">
      <div class="phone-header__left">
        <button class="phone-header__back">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1a1a2e" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="phone-header__info">
          <span class="phone-header__name">HeartBuddy</span>
          <span class="phone-header__online">
            <span class="phone-header__dot" />
            Online
          </span>
        </div>
      </div>
      <button class="phone-header__more">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#1a1a2e" stroke="none">
          <circle cx="12" cy="5" r="2"/>
          <circle cx="12" cy="12" r="2"/>
          <circle cx="12" cy="19" r="2"/>
        </svg>
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="phone-error">
      <span>⚠️ {{ error }}</span>
    </div>

    <!-- 消息列表 -->
    <ChatMessageList
      :messages="messages"
      :current-streaming="currentStreaming"
      :is-loading="isLoading"
    />

    <!-- 输入区 -->
    <ChatInput :is-loading="isLoading" @send="(text, entry) => emit('send', text, entry)" />
  </div>
</template>

<style scoped>
.phone-simulator {
  width: 375px;
  height: 700px;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 36px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.phone-statusbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px 2px;
  font-size: 14px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.65);
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
}

.phone-statusbar__icons {
  display: flex;
  align-items: center;
  gap: 5px;
  color: rgba(0, 0, 0, 0.65);
}

.phone-statusbar__5g {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.phone-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 12px 10px 12px;
}

.phone-header__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.phone-header__back {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.8);
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.phone-header__info {
  display: flex;
  flex-direction: column;
}

.phone-header__name {
  font-size: 16px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.8);
  line-height: 1.3;
}

.phone-header__online {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
}

.phone-header__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3fb950;
  flex-shrink: 0;
}

.phone-header__more {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.6);
}

.phone-error {
  padding: 6px 12px;
  background: #fef2f2;
  box-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
  color: #dc2626;
  font-size: 12px;
  text-align: center;
}
</style>
