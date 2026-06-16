<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  ArrowDownTrayIcon,
  CalendarDaysIcon,
  CheckBadgeIcon,
  ChevronDownIcon,
  ClipboardDocumentCheckIcon,
  ClockIcon,
  CpuChipIcon,
  LanguageIcon,
  SunIcon,
  TrashIcon,
  UserCircleIcon,
} from '@heroicons/vue/24/outline'
import { useConversationSession } from './composables/useConversationSession'
import type { Message, StructuredMainTaskOutput } from './types/app'

const {
  isInitializing,
  isLoading,
  messages,
  resetConversationSession,
  sendMessage: sendConversationMessage,
  structuredTaskOutput,
  userInput,
} = useConversationSession()

const expandedTaskOrders = ref<number[]>([])
const loadingElapsedSeconds = ref(0)
const showResetConversationDialog = ref(false)
let loadingTimer: ReturnType<typeof setInterval> | null = null

const sendMessage = async () => {
  await sendConversationMessage()
}

const noop = () => {}

const openResetConversationDialog = () => {
  showResetConversationDialog.value = true
}

const closeResetConversationDialog = () => {
  showResetConversationDialog.value = false
}

const confirmResetConversation = () => {
  showResetConversationDialog.value = false
  resetConversationSession()
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

watch(isLoading, value => {
  if (loadingTimer) {
    clearInterval(loadingTimer)
    loadingTimer = null
  }

  if (!value) {
    loadingElapsedSeconds.value = 0
    return
  }

  loadingElapsedSeconds.value = 0
  loadingTimer = setInterval(() => {
    loadingElapsedSeconds.value += 1
  }, 1000)
})

onBeforeUnmount(() => {
  if (loadingTimer) {
    clearInterval(loadingTimer)
  }
})

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

const footerTotalEstimatedTimeLabel = computed(
  () =>
    structuredTaskOutput.value?.summary_metrics.total_estimated_time_text
    ?? totalEstimatedTimeLabel.value
    ?? '待確認',
)

const footerDailyTimeBudgetLabel = computed(
  () => structuredTaskOutput.value?.summary_metrics.daily_time_budget_text ?? '待確認',
)

const footerEstimatedCompletionLabel = computed(
  () => structuredTaskOutput.value?.summary_metrics.estimated_completion_text ?? '待確認',
)

const visibleMainTasks = computed<StructuredMainTaskOutput[]>(() => structuredTaskOutput.value?.main_tasks ?? [])

const formatMessageTime = (timestamp?: string): string => {
  if (!timestamp) return '--:--'

  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return '--:--'

  return new Intl.DateTimeFormat('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

const formatLoadingElapsed = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds} 秒`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes} 分 ${remainingSeconds} 秒`
}

const getMessageRoleLabel = (message: Message): string => {
  if (message.type === 'user') return '你'
  if (message.type === 'ai') return '助手'
  return '系統'
}
</script>

<template>
  <div class="app-container">
    <!-- 左側聊天區 -->
    <div class="chat-section">
      <div class="chat-header">
        <div class="chat-header-brand">
          <div class="chat-brand-mark" aria-hidden="true">
            <ClipboardDocumentCheckIcon class="ui-icon ui-icon-brand" />
          </div>
          <div>
            <div class="chat-title-row">
              <h1>任務規劃助手</h1>
              <span class="beta-badge">beta</span>
            </div>
            <p>您的學習與專案規劃夥伴</p>
          </div>
        </div>

        <div class="chat-header-actions">
          <button class="header-action-button" type="button" @click="noop" aria-label="切換語言">
            <LanguageIcon class="ui-icon" />
            <span>中文</span>
            <ChevronDownIcon class="ui-icon ui-icon-inline" />
          </button>
          <button class="header-action-button icon-only-button" type="button" @click="noop" aria-label="切換主題">
            <SunIcon class="ui-icon" />
          </button>
          <button
            class="header-action-button icon-only-button danger-button"
            type="button"
            @click="openResetConversationDialog"
            aria-label="刪除本輪對話"
            :disabled="isLoading || isInitializing"
          >
            <TrashIcon class="ui-icon" />
          </button>
        </div>
      </div>

      <div v-if="isInitializing" class="initializing-state">
        <p>正在初始化對話...</p>
      </div>
      <div v-else class="chat-messages">
        <div v-for="message in messages" :key="message.id" :class="['message', message.type]">
          <div class="message-shell">
            <div class="message-avatar" :class="`avatar-${message.type}`">
              <UserCircleIcon v-if="message.type === 'user'" class="message-avatar-icon" />
              <CpuChipIcon v-else class="message-avatar-icon" />
            </div>
            <div class="message-body">
              <div class="message-meta-row">
                <span class="message-role">{{ getMessageRoleLabel(message) }}</span>
                <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
              </div>
              <div class="message-bubble">
                {{ message.content }}
              </div>
            </div>
          </div>
        </div>
        <div v-if="isLoading" class="message ai loading">
          <div class="message-shell">
            <div class="message-avatar avatar-ai">
              <CpuChipIcon class="message-avatar-icon" />
            </div>
            <div class="message-body">
              <div class="message-meta-row">
                <span class="message-role">助手</span>
                <span class="message-time">處理中</span>
              </div>
              <div class="message-bubble">
                AI 正在思考中，已等待 {{ formatLoadingElapsed(loadingElapsedSeconds) }}...
              </div>
            </div>
          </div>
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
        <div class="planning-header-copy">
          <div class="planning-header-title-row">
            <h2>任務規劃面板</h2>
          </div>
        </div>
      </div>

      <div v-if="!structuredTaskOutput || structuredTaskOutput.main_tasks.length === 0" class="no-planning-state">
        <p>尚未有規劃任務</p>
        <p>請在左側聊天區輸入目標，例如「java作業 7天完成」。</p>
      </div>

      <div v-else class="planning-content">
        <div class="planning-summary-card">
          <div class="planning-summary-header">
            <div class="planning-summary-icon" aria-hidden="true">
              <CheckBadgeIcon class="ui-icon ui-icon-brand" />
            </div>
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
                  <ClockIcon class="time-icon-svg" />
                  <span class="plan-time">{{ normalizeEstimatedTimeLabel(mainTask.estimated_time) }}</span>
                </div>
              </div>
              <ChevronDownIcon class="task-expand-indicator" :class="{ open: isTaskExpanded(mainTask.order) }" />
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
                  <ClockIcon class="time-icon-svg" />
                  <span class="subtask-time">{{ normalizeEstimatedTimeLabel(subtask.estimated_time) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>

        <div class="planning-footer">
          <div class="planning-footer-item">
            <ClockIcon class="footer-icon" />
            <span>總預估時間：{{ footerTotalEstimatedTimeLabel }}</span>
          </div>
          <div class="planning-footer-item">
            <ClockIcon class="footer-icon" />
            <span>每日投入：{{ footerDailyTimeBudgetLabel }}</span>
          </div>
          <div class="planning-footer-item">
            <CalendarDaysIcon class="footer-icon" />
            <span>預計完成：{{ footerEstimatedCompletionLabel }}</span>
          </div>
          <div class="planning-footer-actions">
            <button class="planning-export-button" type="button" @click="noop">
              <ArrowDownTrayIcon class="footer-icon footer-icon-button" />
              <span>匯出計畫</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div
    v-if="showResetConversationDialog"
    class="dialog-overlay"
    @click.self="closeResetConversationDialog"
  >
    <div class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="reset-conversation-title">
      <div class="confirm-dialog-header">
        <div class="confirm-dialog-icon" aria-hidden="true">
          <TrashIcon class="ui-icon ui-icon-brand" />
        </div>
        <div>
          <h3 id="reset-conversation-title">刪除本輪對話？</h3>
          <p>這會清除前端保存的 `conversation_id` 並重新整理頁面，方便快速切換 demo 情境。</p>
        </div>
      </div>
      <div class="confirm-dialog-actions">
        <button class="dialog-secondary-button" type="button" @click="closeResetConversationDialog">
          取消
        </button>
        <button class="dialog-primary-button danger-fill-button" type="button" @click="confirmResetConversation">
          刪除並重新整理
        </button>
      </div>
    </div>
  </div>
</template>
