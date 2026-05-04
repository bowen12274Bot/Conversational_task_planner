<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { sendUserRequest, createConversation, getConversationHistory } from './services/api'

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

// MVP Phase 2: 对话缓存和历史加载
const conversationId = ref<string | null>(null)
const isInitializing = ref(true)

// 缓存键名
const CONVERSATION_CACHE_KEY = 'conversation_cache'
const CONVERSATION_ID_KEY = 'conversation_id'

// 对话缓存接口
interface ConversationCache {
  messages: Message[]
  planTasks: PlanTask[]
  lastUpdated: string
}

// 缓存管理函数
const saveConversationCache = () => {
  const cache: ConversationCache = {
    messages: messages.value,
    planTasks: planTasks.value,
    lastUpdated: new Date().toISOString()
  }
  localStorage.setItem(CONVERSATION_CACHE_KEY, JSON.stringify(cache))
  if (conversationId.value) {
    localStorage.setItem(CONVERSATION_ID_KEY, conversationId.value)
  }
}

const loadConversationCache = (): ConversationCache | null => {
  const cacheStr = localStorage.getItem(CONVERSATION_CACHE_KEY)
  const conversationIdStr = localStorage.getItem(CONVERSATION_ID_KEY)

  if (cacheStr && conversationIdStr) {
    try {
      const cache = JSON.parse(cacheStr) as ConversationCache
      conversationId.value = conversationIdStr
      return cache
    } catch (error) {
      console.error('Failed to parse conversation cache:', error)
      clearConversationCache()
    }
  }
  return null
}

const clearConversationCache = () => {
  localStorage.removeItem(CONVERSATION_CACHE_KEY)
  localStorage.removeItem(CONVERSATION_ID_KEY)
  conversationId.value = null
}

// 初始化对话
const initializeConversation = async () => {
  try {
    // 尝试从缓存加载
    const cache = loadConversationCache()
    if (cache) {
      // 如果有缓存，尝试从服务器加载最新历史
      if (conversationId.value) {
        try {
          const history = await getConversationHistory(conversationId.value)
          // 使用服务器的历史数据重建界面
          messages.value = history.messages.map(msg => ({
            id: parseInt(msg.id),
            type: msg.type,
            content: msg.content
          }))

          if (history.plan_tasks) {
            planTasks.value = history.plan_tasks.map(task => ({
              id: task.id,
              title: task.title,
              due: task.due,
              createdAt: new Date(task.created_at),
              subtasks: task.subtasks.map(sub => ({
                id: sub.id,
                title: sub.title,
                description: sub.description,
                priority: sub.priority,
                estimatedTime: sub.estimated_time,
                completed: sub.completed
              }))
            }))
          }
        } catch (error) {
          console.warn('Failed to load conversation history, using cache:', error)
          // 如果服务器加载失败，使用缓存数据
          messages.value = cache.messages
          planTasks.value = cache.planTasks
        }
      }
    } else {
      // 没有缓存，创建新对话
      conversationId.value = await createConversation()
      saveConversationCache()
    }
  } catch (error) {
    console.error('Failed to initialize conversation:', error)
    // 创建新对话作为后备
    try {
      conversationId.value = await createConversation()
      saveConversationCache()
    } catch (fallbackError) {
      console.error('Failed to create fallback conversation:', fallbackError)
    }
  } finally {
    isInitializing.value = false
  }
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const inputText = userInput.value.trim()
  userInput.value = ''

  const userMessage: Message = {
    id: Date.now(),
    type: 'user',
    content: inputText
  }

  messages.value.push(userMessage)
  saveConversationCache() // 立即保存缓存

  // 先生成任務與子任務，再呼叫後端API顯示AI回應
  parseAndAddPlan(inputText)
  saveConversationCache() // 保存任务更新

  isLoading.value = true

  try {
    const response = await sendUserRequest(inputText)
    const aiMessage: Message = {
      id: Date.now() + 1,
      type: 'ai',
      content: response.reply_text
    }
    messages.value.push(aiMessage)
    saveConversationCache() // 保存AI回复
  } catch (error) {
    const errorMessage: Message = {
      id: Date.now() + 1,
      type: 'ai',
      content: `抱歉，發生錯誤：${error instanceof Error ? error.message : '未知錯誤'}`
    }
    messages.value.push(errorMessage)
    saveConversationCache() // 保存错误消息
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
    saveConversationCache() // 保存任务状态变更
  }
}

// 组件挂载时初始化对话
onMounted(async () => {
  await initializeConversation()
})
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
