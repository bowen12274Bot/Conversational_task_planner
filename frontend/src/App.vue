<script setup lang="ts">
import { ref, computed } from 'vue'
import { sendUserRequest } from './services/api'

type Message = {
  id: number
  type: 'system' | 'user' | 'ai'
  content: string
}

type Task = {
  id: string
  title: string
  description?: string
  priority?: number
  estimatedTime?: string
  completed: boolean
  createdAt: Date
}

const messages = ref<Message[]>([
  { id: 1, type: 'system', content: '歡迎使用對話式任務規劃系統！請輸入您的作業或小專題目標。' }
])

const userInput = ref('')
const isLoading = ref(false)
const tasks = ref<Task[]>([])

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const inputText = userInput.value.trim()
  userInput.value = ''

  // 添加用戶訊息
  messages.value.push({
    id: Date.now(),
    type: 'user',
    content: inputText
  })

  isLoading.value = true

  try {
    // 呼叫後端API
    const response = await sendUserRequest(inputText)

    // 添加AI回應
    messages.value.push({
      id: Date.now() + 1,
      type: 'ai',
      content: response.reply_text
    })

    // 解析並更新任務列表 - 無論是否有structured_task_output都嘗試生成任務
    parseAndAddTasks(inputText)
  } catch (error) {
    // 錯誤處理
    messages.value.push({
      id: Date.now() + 1,
      type: 'ai',
      content: `抱歉，發生錯誤：${error instanceof Error ? error.message : '未知錯誤'}`
    })
  } finally {
    isLoading.value = false
  }
}

const parseAndAddTasks = (userInput: string) => {
  // 根據用戶輸入生成相關任務
  const newTasks: Task[] = []

  // 檢查用戶輸入是否包含java作業相關關鍵字
  if (userInput.toLowerCase().includes('java') && userInput.includes('作業')) {
    newTasks.push(
      {
        id: `task-${Date.now()}-1`,
        title: '學習Java基礎語法',
        description: '掌握變數、資料型別、運算子等基礎概念',
        priority: 1,
        estimatedTime: '2小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-2`,
        title: '完成Java作業練習',
        description: '實作指定作業題目',
        priority: 2,
        estimatedTime: '3小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-3`,
        title: '程式碼測試與除錯',
        description: '確保程式正確運行並修復錯誤',
        priority: 3,
        estimatedTime: '1小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-4`,
        title: '作業提交與複習',
        description: '提交作業並複習學習內容',
        priority: 4,
        estimatedTime: '1小時',
        completed: false,
        createdAt: new Date()
      }
    )
  } else if (userInput.includes('作業') || userInput.includes('專題') || userInput.includes('報告')) {
    // 通用作業/專題任務
    newTasks.push(
      {
        id: `task-${Date.now()}-1`,
        title: '分析需求與規劃',
        description: '理解任務要求並制定初步計劃',
        priority: 1,
        estimatedTime: '1小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-2`,
        title: '收集資料與研究',
        description: '蒐集相關資訊和參考資料',
        priority: 2,
        estimatedTime: '2小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-3`,
        title: '執行與實作',
        description: '按照計劃執行任務內容',
        priority: 3,
        estimatedTime: '4小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-4`,
        title: '檢查與修改',
        description: '檢查成果並進行必要的修改',
        priority: 4,
        estimatedTime: '1小時',
        completed: false,
        createdAt: new Date()
      },
      {
        id: `task-${Date.now()}-5`,
        title: '完成與提交',
        description: '最終檢查並提交作業',
        priority: 5,
        estimatedTime: '30分鐘',
        completed: false,
        createdAt: new Date()
      }
    )
  }

  // 如果有生成的任務，添加到任務列表
  if (newTasks.length > 0) {
    tasks.value.push(...newTasks)
  }
}

const toggleTaskCompletion = (taskId: string) => {
  const task = tasks.value.find(t => t.id === taskId)
  if (task) {
    task.completed = !task.completed
  }
}

const deleteTask = (taskId: string) => {
  const index = tasks.value.findIndex(t => t.id === taskId)
  if (index > -1) {
    tasks.value.splice(index, 1)
  }
}

const completedTasks = computed(() => tasks.value.filter(task => task.completed))
const pendingTasks = computed(() => tasks.value.filter(task => !task.completed))

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('zh-TW', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

      <!-- 無任務狀態 -->
      <div v-if="tasks.length === 0" class="no-planning-state">
        <p>尚未有規劃任務</p>
        <p>請在左側聊天區輸入目標，系統將協助您進行任務拆解與規劃。</p>
      </div>

      <!-- 有任務時顯示 -->
      <div v-else class="tasks-container">
        <!-- 未完成任務 -->
        <div v-if="pendingTasks.length > 0" class="task-section">
          <h3 class="section-title pending">未完成任務 ({{ pendingTasks.length }})</h3>
          <div class="task-list">
            <div
              v-for="task in pendingTasks"
              :key="task.id"
              :class="['task-item', { 'high-priority': task.priority === 1 }]"
            >
              <div class="task-header">
                <input
                  type="checkbox"
                  :checked="task.completed"
                  @change="toggleTaskCompletion(task.id)"
                  class="task-checkbox"
                />
                <span class="task-priority" :class="'priority-' + task.priority">{{ task.priority }}</span>
                <h4 class="task-title">{{ task.title }}</h4>
                <button @click="deleteTask(task.id)" class="delete-btn" title="刪除任務">×</button>
              </div>
              <p v-if="task.description" class="task-description">{{ task.description }}</p>
              <div class="task-meta">
                <span v-if="task.estimatedTime" class="task-time">預估時間：{{ task.estimatedTime }}</span>
                <span class="task-date">{{ formatDate(task.createdAt) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 已完成任務 -->
        <div v-if="completedTasks.length > 0" class="task-section">
          <h3 class="section-title completed">已完成任務 ({{ completedTasks.length }})</h3>
          <div class="task-list">
            <div
              v-for="task in completedTasks"
              :key="task.id"
              class="task-item completed"
            >
              <div class="task-header">
                <input
                  type="checkbox"
                  :checked="task.completed"
                  @change="toggleTaskCompletion(task.id)"
                  class="task-checkbox"
                />
                <span class="task-priority" :class="'priority-' + task.priority">{{ task.priority }}</span>
                <h4 class="task-title completed-text">{{ task.title }}</h4>
                <button @click="deleteTask(task.id)" class="delete-btn" title="刪除任務">×</button>
              </div>
              <p v-if="task.description" class="task-description completed-text">{{ task.description }}</p>
              <div class="task-meta">
                <span v-if="task.estimatedTime" class="task-time">預估時間：{{ task.estimatedTime }}</span>
                <span class="task-date">{{ formatDate(task.createdAt) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
