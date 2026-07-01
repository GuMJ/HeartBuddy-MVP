<script setup lang="ts">
/**
 * App.vue — HeartBuddy 主页面
 *
 * 毛玻璃双栏布局：手机模拟器 + 监控台
 */
import { ref, onMounted } from "vue";
import PhoneSimulator from "./components/PhoneSimulator.vue";
import MonitorConsole from "./components/MonitorConsole.vue";
import { useChat } from "./composables/useChat";

const sessionId = ref("");

async function createSession() {
  try {
    const res = await fetch("/api/sessions", { method: "POST" });
    const data = (await res.json()) as { session_id: string };
    sessionId.value = data.session_id;
  } catch (err) {
    sessionId.value = "local-" + Date.now().toString(36);
  }
}

onMounted(() => createSession());

const {
  messages,
  isLoading,
  currentStreaming,
  error,
  send,
} = useChat(sessionId);
</script>

<template>
  <div class="app">
    <!-- 背景光斑 -->
    <div class="bg-blob bg-blob--1" />
    <div class="bg-blob bg-blob--2" />
    <div class="bg-blob bg-blob--3" />

    <!-- 主内容 -->
    <div class="app__content">
      <div class="panel">
        <PhoneSimulator
          :messages="messages"
          :current-streaming="currentStreaming"
          :is-loading="isLoading"
          :error="error"
          @send="send"
        />
      </div>
      <div class="panel">
        <MonitorConsole />
      </div>
    </div>
  </div>
</template>

<style scoped>
.app {
  position: relative;
  min-height: 100vh;
  background: #f0f4f0;
  overflow: hidden;
}

/* ---- 背景光斑 ---- */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
}

.bg-blob--1 {
  width: 1200px;
  height: 1200px;
  background: radial-gradient(circle at center, #4ade80 0%, transparent 50%);
  top: -600px;
  left: -400px;
  opacity: 0.65;
}

.bg-blob--2 {
  width: 2000px;
  height: 2000px;
  background: radial-gradient(circle at center, #3b82f6 0%, transparent 45%);
  bottom: -1000px;
  left: -700px;
  opacity: 0.6;
}

.bg-blob--3 {
  width: 2600px;
  height: 2600px;
  background: radial-gradient(circle at center, #8b5cf6 0%, transparent 45%);
  bottom: -1300px;
  right: -1000px;
  opacity: 0.55;
}

/* ---- 主布局 ---- */
.app__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 24px;
  padding: 24px;
}

.panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 560px;
}
</style>
