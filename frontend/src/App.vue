<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useConversationSession } from './composables/useConversationSession'
import { mockStructuredTaskOutput } from './utils/mockStructuredTaskOutput'
import type { StructuredMainTaskOutput } from './types/app'

const {
  isInitializing,
  isLoading,
  messages,
  sendMessage: sendConversationMessage,
  setStructuredTaskOutput,
  structuredTaskOutput,
  userInput,
} = useConversationSession()

const isDev = import.meta.env.DEV
const expandedTaskOrders = ref<number[]>([])

const sendMessage = async () => {
  await sendConversationMessage()
}

const loadMockPlanningPreview = () => {
  setStructuredTaskOutput(mockStructuredTaskOutput)
}

watch(
  structuredTaskOutput,
  value => {
    if (!value || value.main_tasks.length === 0) {
      expandedTaskOrders.value = []
      return
    }

    expandedTaskOrders.value = value.main_tasks.slice(0, 3).map(task => task.order)
  },
  { immediate: true },
)

const priorityLabelMap = {
  high: '高',
  medium: '中',
  low: '低',
} as const

const isTaskExpanded = (taskOrder: number) => expandedTaskOrders.value.includes(taskOrder)

const toggleTaskExpanded = (taskOrder: number) => {
  if (isTaskExpanded(taskOrder)) {
    expandedTaskOrders.value = expandedTaskOrders.value.filter(order => order !== taskOrder)
    return
  }

  expandedTaskOrders.value = [...expandedTaskOrders.value, taskOrder].sort((a, b) => a - b)
}

const parseEstimatedTimeToMinutes = (value: string): number | null => {
  const normalized = value.trim().toLowerCase()
  if (!normalized) return null

  const rangeMatch = normalized.match(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)/)
  const rangeAverage = rangeMatch
    ? (Number(rangeMatch[1]) + Number(rangeMatch[2])) / 2
    : null

  if (normalized.includes('分鐘') || normalized.includes('min') || normalized.endsWith('m')) {
    const base = rangeAverage ?? Number(normalized.match(/\d+(?:\.\d+)?/)?.[0] ?? NaN)
    return Number.isFinite(base) ? Math.round(base) : null
  }

  if (normalized.includes('小時') || normalized.includes('hour') || normalized.endsWith('h')) {
    const base = rangeAverage ?? Number(normalized.match(/\d+(?:\.\d+)?/)?.[0] ?? NaN)
    return Number.isFinite(base) ? Math.round(base * 60) : null
  }

  const plainNumber = Number(normalized.match(/\d+(?:\.\d+)?/)?.[0] ?? NaN)
  return Number.isFinite(plainNumber) ? Math.round(plainNumber * 60) : null
}

const formatMinutesLabel = (minutes: number): string => {
  if (minutes < 60) {
    return `約 ${minutes} 分鐘`
  }

  const hours = minutes / 60
  const rounded = Math.round(hours * 10) / 10
  const display = Number.isInteger(rounded) ? `${rounded.toFixed(0)}` : `${rounded.toFixed(1)}`
  return `約 ${display} 小時`
}

const normalizeEstimatedTimeLabel = (value: string): string => {
  const normalized = value.trim()
  if (!normalized) return value

  return normalized
    .replace(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*h\b/gi, '$1-$2 小時')
    .replace(/(\d+(?:\.\d+)?)\s*h\b/gi, '$1 小時')
    .replace(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*m\b/gi, '$1-$2 分鐘')
    .replace(/(\d+(?:\.\d+)?)\s*m\b/gi, '$1 分鐘')
}

const totalEstimatedMinutes = computed(() => {
  if (!structuredTaskOutput.value) return null

  const allSubtasks = structuredTaskOutput.value.main_tasks.flatMap(task => task.subtasks)
  const subtaskMinutes = allSubtasks
    .map(subtask => parseEstimatedTimeToMinutes(subtask.estimated_time))
    .filter((value): value is number => value !== null)

  if (subtaskMinutes.length > 0) {
    return subtaskMinutes.reduce((sum, value) => sum + value, 0)
  }

  const mainTaskMinutes = structuredTaskOutput.value.main_tasks
    .map(task => parseEstimatedTimeToMinutes(task.estimated_time))
    .filter((value): value is number => value !== null)

  if (mainTaskMinutes.length === 0) return null
  return mainTaskMinutes.reduce((sum, value) => sum + value, 0)
})

const totalEstimatedTimeLabel = computed(() =>
  totalEstimatedMinutes.value === null ? null : formatMinutesLabel(totalEstimatedMinutes.value),
)

const visibleMainTasks = computed<StructuredMainTaskOutput[]>(() => structuredTaskOutput.value?.main_tasks ?? [])
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
      <div class="planning-panel-header">
        <div>
          <h2>任務規劃面板</h2>
        </div>

        <div v-if="isDev" class="planning-dev-tools">
          <button class="planning-dev-button" type="button" @click="loadMockPlanningPreview">
            載入 mock 規劃
          </button>
        </div>
      </div>

      <div v-if="!structuredTaskOutput || structuredTaskOutput.main_tasks.length === 0" class="no-planning-state">
        <p>尚未有規劃任務</p>
        <p>請在左側聊天區輸入目標，例如「java作業 7天完成」。</p>
      </div>

      <div v-else class="planning-content">
        <div class="planning-summary-card">
          <div class="planning-summary-header">
            <div class="planning-summary-icon" aria-hidden="true"></div>
            <div>
              <p class="planning-summary-title">規劃總結 Summary</p>
              <p class="planning-summary-text">{{ structuredTaskOutput.plan_summary }}</p>
            </div>
          </div>
        </div>

        <div class="plan-task-list">
        <div
          v-for="mainTask in visibleMainTasks"
          :key="`${mainTask.order}-${mainTask.title}`"
          class="plan-task-card"
        >
          <button class="plan-task-header" type="button" @click="toggleTaskExpanded(mainTask.order)">
            <div class="plan-task-header-left">
              <div class="plan-order-badge">{{ mainTask.order }}</div>
              <div class="plan-task-copy">
                <h3 class="plan-title">{{ mainTask.title }}</h3>
                <p class="plan-meta">{{ mainTask.description }}</p>
              </div>
            </div>

            <div class="plan-task-header-right">
              <div class="plan-time-block">
                <span class="plan-time-label">預估時間</span>
                <div class="plan-time-row">
                  <span class="time-icon" aria-hidden="true">◔</span>
                  <span class="plan-time">{{ normalizeEstimatedTimeLabel(mainTask.estimated_time) }}</span>
                </div>
              </div>
              <span class="task-expand-indicator" :class="{ open: isTaskExpanded(mainTask.order) }">⌄</span>
            </div>
          </button>

          <div v-if="isTaskExpanded(mainTask.order)" class="subtask-panel">
            <div class="subtask-summary">
              <span class="subtask-summary-label">子任務</span>
              <span class="subtask-summary-meta">{{ mainTask.subtasks.length }} 項</span>
            </div>

            <div class="subtask-list">
              <div
                v-for="subtask in mainTask.subtasks"
                :key="`${mainTask.order}-${subtask.order}-${subtask.title}`"
                class="subtask-item"
              >
                <div class="subtask-sequence">{{ mainTask.order }}.{{ subtask.order }}</div>
                <div class="subtask-content">
                  <div class="subtask-title-row">
                    <h4 class="subtask-title">{{ subtask.title }}</h4>
                    <span class="subtask-priority" :class="`priority-${subtask.priority}`">
                      {{ priorityLabelMap[subtask.priority] }}
                    </span>
                  </div>
                  <p class="subtask-description">{{ subtask.description }}</p>
                </div>
                <div class="subtask-time-box">
                  <span class="time-icon" aria-hidden="true">◔</span>
                  <span class="subtask-time">{{ normalizeEstimatedTimeLabel(subtask.estimated_time) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>

        <div class="planning-footer">
          <div v-if="totalEstimatedTimeLabel" class="planning-footer-item">
            <span class="footer-icon" aria-hidden="true">◔</span>
            <span>總預估時間：{{ totalEstimatedTimeLabel }}</span>
          </div>
          <div class="plan-title-block">
            <span class="footer-icon" aria-hidden="true">◷</span>
            <span>已整理 {{ visibleMainTasks.length }} 個主要任務</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
