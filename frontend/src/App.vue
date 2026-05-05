<script setup lang="ts">
import { useConversationSession } from './composables/useConversationSession'
import { useTemporaryPlanning } from './utils/temporaryPlanning'

const {
  isInitializing,
  isLoading,
  messages,
  sendMessage: sendConversationMessage,
  userInput,
} = useConversationSession()

const {
  addPlanTask,
  planTasks,
  toggleSubtaskCompletion,
} = useTemporaryPlanning()

const showTemporaryPlanning = false

const sendMessage = async () => {
  const result = await sendConversationMessage()

  if (result.ok) {
    addPlanTask(result.inputText)
  }
}
</script>

<template>
  <div class="app-container">
    <!-- 左側聊天區 -->
    <div class="chat-section">
      <div v-if="isInitializing" class="initializing-state">
        <p>正在初始化對話...</p>
      </div>
      <div v-else class="chat-messages">
        <div v-for="message in messages" :key="message.id" :class="['message', message.type]">
          {{ message.content }}
        </div>
        <div v-if="isLoading" class="message ai loading">
          AI 正在思考中...
        </div>
      </div>
      <div class="chat-input">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage"
          :disabled="isLoading || isInitializing"
          placeholder="輸入您的目標或問題..."
          type="text"
        />
        <button @click="sendMessage" :disabled="isLoading || isInitializing || !userInput.trim()">
          {{ isLoading ? '處理中...' : '送出' }}
        </button>
      </div>
    </div>

    <!-- 右側規劃面板 -->
    <div class="planning-panel">
      <h2>任務規劃面板</h2>

      <div v-if="!showTemporaryPlanning || planTasks.length === 0" class="no-planning-state">
        <p>尚未有規劃任務</p>
        <p>請在左側聊天區輸入目標，例如「java作業 7天完成」。</p>
      </div>

      <div v-else class="plan-task-list">
        <div v-for="plan in planTasks" :key="plan.id" class="plan-task-card">
          <div class="plan-task-header">
            <div>
              <p class="plan-label">主要任務</p>
              <h3 class="plan-title">{{ plan.title }}</h3>
              <p v-if="plan.due" class="plan-meta">期限：{{ plan.due }}</p>
            </div>
            <div class="plan-stats">
              <span>{{ plan.subtasks.filter(sub => !sub.completed).length }} 未完成</span>
              <span>{{ plan.subtasks.filter(sub => sub.completed).length }} 已完成</span>
            </div>
          </div>

          <div class="subtask-list">
            <div v-for="subtask in plan.subtasks" :key="subtask.id" :class="['subtask-item', { completed: subtask.completed }]">
              <label class="subtask-row">
                <input
                  type="checkbox"
                  :checked="subtask.completed"
                  @change="toggleSubtaskCompletion(plan.id, subtask.id)"
                />
                <div class="subtask-content">
                  <div class="subtask-title-row">
                    <span class="subtask-priority" :class="'priority-' + subtask.priority">{{ subtask.priority }}</span>
                    <h4 class="subtask-title">{{ subtask.title }}</h4>
                  </div>
                  <p v-if="subtask.description" class="subtask-description">{{ subtask.description }}</p>
                </div>
                <span class="subtask-time" v-if="subtask.estimatedTime">{{ subtask.estimatedTime }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
