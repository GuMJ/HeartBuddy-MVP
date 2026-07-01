<script setup lang="ts">
import { ref, nextTick } from "vue";

const emit = defineEmits<{
  send: [text: string];
}>();

defineProps<{
  isLoading: boolean;
}>();

const inputText = ref("");
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const tools = [
  { label: "缓解紧张" },
  { label: "提升自信" },
  { label: "学会拒绝" },
  { label: "发现热爱" },
];

function autoGrow() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text) return;
  emit("send", text);
  inputText.value = "";
  const el = textareaRef.value;
  if (el) el.style.height = "auto";
  await nextTick();
  textareaRef.value?.focus();
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSend();
  }
}

function selectTool(label: string) {
  inputText.value = `我想${label}`;
  autoGrow();
  textareaRef.value?.focus();
}
</script>

<template>
  <div class="input-area">
    <!-- 工具标签 -->
    <div class="tool-chips">
      <button
        v-for="tool in tools"
        :key="tool.label"
        class="tool-chip"
        @click="selectTool(tool.label)"
      >
        {{ tool.label }}
      </button>
    </div>

    <!-- 输入框 -->
    <div class="input-box">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="input-box__textarea"
        placeholder="Message…"
        rows="1"
        @input="autoGrow"
        @keydown="handleKeydown"
      />

      <button
        class="input-box__send"
        :class="{ active: inputText.trim() && !isLoading }"
        :disabled="!inputText.trim() || isLoading"
        @click="handleSend"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5"/>
          <polyline points="5 12 12 5 19 12"/>
        </svg>
      </button>
    </div>

    <!-- 免责声明 -->
    <p class="input-area__disclaimer">AI may produce inaccurate responses. Use discretion.</p>
  </div>
</template>

<style scoped>
.input-area {
  padding: 4px 16px 8px;
}

/* ---- 工具标签 ---- */
.tool-chips {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.tool-chip {
  padding: 5px 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  color: #1a1a2e;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}


/* ---- 输入框 ---- */
.input-box {
  position: relative;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 20px;
  padding: 10px 52px 10px 12px;
}

.input-box__textarea {
  width: 100%;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  color: #1a1a2e;
  font-size: 14px;
  line-height: 1.5;
  min-height: 44px;
  max-height: 100px;
  overflow-y: hidden;
  font-family: inherit;
}

.input-box__textarea::placeholder {
  color: rgba(0, 0, 0, 0.45);
}

.input-box__textarea:disabled {
  opacity: 0.4;
}

/* ---- 发送按钮 ---- */
.input-box__send {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #4f8cff, #a855f7);
  color: white;
  opacity: 0.35;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  transition: opacity 0.2s ease;
}

.input-box__send.active {
  opacity: 1;
  cursor: pointer;
}

/* ---- 免责声明 ---- */
.input-area__disclaimer {
  margin: 6px 0 0;
  font-size: 10px;
  color: rgba(0, 0, 0, 0.45);
  text-align: center;
}
</style>
