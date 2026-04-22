<script setup lang="ts">
import { ref } from 'vue'

const messages = ref([
  { id: 1, type: 'system', content: '歡迎使用對話式任務規劃系統！請輸入您的作業或小專題目標。' }
])

const userInput = ref('')

const sendMessage = () => {
  if (userInput.value.trim()) {
    messages.value.push({
      id: Date.now(),
      type: 'user',
      content: userInput.value
    })
    userInput.value = ''
    // 這裡可以添加AI回應邏輯
  }
}
</script>

<template>
  <div class="app-container">
    <!-- 左側聊天區 -->
    <div class="chat-section">
      <div class="chat-messages">
        <div v-for="message in messages" :key="message.id" :class="['message', message.type]">
          {{ message.content }}
        </div>
      </div>
      <div class="chat-input">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage"
          placeholder="輸入您的目標或問題..."
          type="text"
        />
        <button @click="sendMessage">送出</button>
      </div>
    </div>

    <!-- 右側規劃面板 -->
    <div class="planning-panel">
      <h2>任務規劃面板</h2>
      <div class="no-planning-state">
        <p>尚未有規劃任務</p>
        <p>請在左側聊天區輸入目標，系統將協助您進行任務拆解與規劃。</p>
      </div>
      <!-- 預留已有規劃任務狀態的位置 -->
      <div class="planned-tasks-placeholder" style="display: none;">
        <!-- 這裡將放置已規劃的任務列表 -->
      </div>
    </div>
  </div>
</template>
