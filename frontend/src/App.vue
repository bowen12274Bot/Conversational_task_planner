<script setup lang="ts">
import { ref } from 'vue'
import { sendUserRequest } from './services/api'

type Message = {
  id: number
  type: 'system' | 'user' | 'ai'
  content: string
}

type Subtask = {
  id: string
  title: string
  description?: string
  priority: number
  estimatedTime?: string
  completed: boolean
}

type PlanTask = {
  id: string
  title: string
  due?: string
  createdAt: Date
  subtasks: Subtask[]
}

const messages = ref<Message[]>([
  { id: 1, type: 'system', content: '歡迎使用對話式任務規劃系統！請輸入您的作業或小專題目標。' }
])

const userInput = ref('')
const isLoading = ref(false)
const planTasks = ref<PlanTask[]>([])

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const inputText = userInput.value.trim()
  userInput.value = ''

  messages.value.push({
    id: Date.now(),
    type: 'user',
    content: inputText
  })

  // 先生成任務與子任務，再呼叫後端API顯示AI回應
  parseAndAddPlan(inputText)
  isLoading.value = true

  try {
    const response = await sendUserRequest(inputText)
    messages.value.push({
      id: Date.now() + 1,
      type: 'ai',
      content: response.reply_text
    })
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      type: 'ai',
      content: `抱歉，發生錯誤：${error instanceof Error ? error.message : '未知錯誤'}`
    })
  } finally {
    isLoading.value = false
  }
}

const parseAndAddPlan = (userInput: string) => {
  const title = deriveTitle(userInput)
  const due = deriveDue(userInput)
  const newPlan: PlanTask = {
    id: `plan-${Date.now()}`,
    title,
    due,
    createdAt: new Date(),
    subtasks: createSubtasks(userInput)
  }

  planTasks.value.push(newPlan)
}

const deriveTitle = (userInput: string): string => {
  const lower = userInput.toLowerCase()
  if (lower.includes('java') && lower.includes('作業')) {
    return 'Java作業'
  }
  if (lower.includes('作業')) {
    return '作業規劃'
  }
  if (lower.includes('專題')) {
    return '專題規劃'
  }
  return userInput
}

const deriveDue = (userInput: string): string | undefined => {
  const match = userInput.match(/(\d+\s*天(?:完成)?)/)
  return match ? match[1].replace(/\s+/g, '') : undefined
}

const createSubtasks = (userInput: string): Subtask[] => {
  const lower = userInput.toLowerCase()
  const baseId = Date.now()

  if (lower.includes('java') && lower.includes('作業')) {
    return [
      {
        id: `subtask-${baseId}-1`,
        title: '學習Java基礎語法',
        description: '掌握變數、資料型別與運算子',
        priority: 1,
        estimatedTime: '2小時',
        completed: false
      },
      {
        id: `subtask-${baseId}-2`,
        title: '完成指定作業題目',
        description: '實作題目並完成主要功能',
        priority: 2,
        estimatedTime: '3小時',
        completed: false
      },
      {
        id: `subtask-${baseId}-3`,
        title: '程式碼測試與除錯',
        description: '測試程式並修正錯誤',
        priority: 3,
        estimatedTime: '1小時',
        completed: false
      },
      {
        id: `subtask-${baseId}-4`,
        title: '作業提交與複習',
        description: '確認內容後提交並複習學習成果',
        priority: 4,
        estimatedTime: '1小時',
        completed: false
      }
    ]
  }

  return [
    {
      id: `subtask-${baseId}-1`,
      title: '分析需求與規劃',
      description: '理解任務內容與預期成果',
      priority: 1,
      estimatedTime: '1小時',
      completed: false
    },
    {
      id: `subtask-${baseId}-2`,
      title: '收集資料與研究',
      description: '蒐集相關參考資料與素材',
      priority: 2,
      estimatedTime: '2小時',
      completed: false
    },
    {
      id: `subtask-${baseId}-3`,
      title: '執行與實作',
      description: '按照規劃執行任務內容',
      priority: 3,
      estimatedTime: '4小時',
      completed: false
    },
    {
      id: `subtask-${baseId}-4`,
      title: '檢查與修改',
      description: '檢查成果並修正問題',
      priority: 4,
      estimatedTime: '1小時',
      completed: false
    }
  ]
}

const toggleSubtaskCompletion = (planId: string, subtaskId: string) => {
  const plan = planTasks.value.find(p => p.id === planId)
  const subtask = plan?.subtasks.find(s => s.id === subtaskId)
  if (subtask) {
    subtask.completed = !subtask.completed
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
        <div v-if="isLoading" class="message ai loading">
          AI 正在思考中...
        </div>
      </div>
      <div class="chat-input">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage"
          :disabled="isLoading"
          placeholder="輸入您的目標或問題..."
          type="text"
        />
        <button @click="sendMessage" :disabled="isLoading || !userInput.trim()">
          {{ isLoading ? '處理中...' : '送出' }}
        </button>
      </div>
    </div>

    <!-- 右側規劃面板 -->
    <div class="planning-panel">
      <h2>任務規劃面板</h2>

      <div v-if="planTasks.length === 0" class="no-planning-state">
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
