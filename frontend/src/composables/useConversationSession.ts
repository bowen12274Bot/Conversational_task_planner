import { onMounted, ref } from 'vue'
import {
  ApiError,
  createConversation,
  getConversationHistory,
  sendUserRequest,
  subscribeProgressEvents,
} from '../services/api'
import type { Message, ProgressEvent, ProgressEventType, StructuredTaskOutput } from '../types/app'
import {
  clearConversationCache,
  getDefaultMessages,
  loadConversationCache,
  loadConversationId,
  saveConversationCache,
  saveConversationId,
} from '../utils/conversationCache'

export function useConversationSession() {
  const messages = ref<Message[]>(getDefaultMessages())
  const userInput = ref('')
  const isLoading = ref(false)
  const isInitializing = ref(true)
  const conversationId = ref<string | null>(null)
  const progressStatusText = ref('處理中...')
  const structuredTaskOutput = ref<StructuredTaskOutput | null>(null)

  const createMessageId = () =>
    messages.value.reduce((maxId, message) => Math.max(maxId, message.id), 0) + 1

  const createTimestamp = () => new Date().toISOString()

  const persistConversationCache = () => {
    saveConversationCache(messages.value, conversationId.value)
  }

  const progressTextMap: Record<ProgressEventType, string> = {
    request_received: '已收到你的需求',
    context_engineering_started: '正在整理你的需求與背景資訊',
    questioning_started: '正在判斷是否需要補充資訊',
    route_decided: '正在選擇最合適的處理方式',
    planning_started: '正在建立任務規劃',
    revision_started: '正在調整既有規劃',
    chat_started: '正在整理回答內容',
    response_started: '正在準備回覆',
    completed: '處理完成',
    failed: '處理時發生錯誤',
  }

  const createRequestId = () => {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      return crypto.randomUUID()
    }

    return `${Date.now()}-${Math.random().toString(16).slice(2)}`
  }

  const startProgressStream = (
    targetConversationId: string,
    requestId: string,
  ): EventSource | null => {
    try {
      return subscribeProgressEvents(
        targetConversationId,
        requestId,
        (event: ProgressEvent) => {
          progressStatusText.value = progressTextMap[event.event_type] ?? '處理中...'
          if (event.event_type === 'completed' || event.event_type === 'failed') {
            progressStream?.close()
            progressStream = null
          }
        },
        () => {
          progressStatusText.value = '處理中...'
          progressStream?.close()
          progressStream = null
        },
      )
    } catch (error) {
      console.error('Failed to start progress stream:', error)
      return null
    }
  }

  let progressStream: EventSource | null = null

  const applyHistoryMessages = async (currentConversationId: string) => {
    const history = await getConversationHistory(currentConversationId)
    let nextMessageId = 1
    const historyMessages = history.turns.flatMap(turn =>
      turn.messages.map(msg => ({
        id: nextMessageId++,
        type: msg.type,
        content: msg.content,
        timestamp: msg.created_at,
      })),
    )

    messages.value = historyMessages.length > 0
      ? historyMessages
      : getDefaultMessages()
    structuredTaskOutput.value = history.structured_task_output ?? null

    saveConversationCache(messages.value, currentConversationId)
  }

  const rebuildConversation = async () => {
    clearConversationCache()
    conversationId.value = await createConversation()
    saveConversationId(conversationId.value)
    messages.value = getDefaultMessages()
    structuredTaskOutput.value = null
    persistConversationCache()
  }

  const initializeConversation = async () => {
    try {
      const existingConversationId = loadConversationId()
      if (existingConversationId) {
        conversationId.value = existingConversationId

        try {
          await applyHistoryMessages(conversationId.value)
        } catch (error) {
          if (error instanceof ApiError && error.status === 404) {
            await rebuildConversation()
          } else {
            try {
              await applyHistoryMessages(conversationId.value)
            } catch (retryError) {
              const cachedConversation = loadConversationCache()
              if (cachedConversation) {
                messages.value = cachedConversation.cache.messages.length > 0
                  ? cachedConversation.cache.messages
                  : getDefaultMessages()
              }
              console.error('Failed to load conversation history:', retryError)
            }
          }
        }
      } else {
        conversationId.value = await createConversation()
        saveConversationId(conversationId.value)
        persistConversationCache()
      }
    } catch (error) {
      try {
        conversationId.value = await createConversation()
        saveConversationId(conversationId.value)
        persistConversationCache()
      } catch (fallbackError) {
        console.error('Failed to create fallback conversation:', fallbackError)
      }
    } finally {
      isInitializing.value = false
    }
  }

  const appendErrorMessage = (error: unknown) => {
    messages.value.push({
      id: createMessageId(),
      type: 'ai',
      content: `抱歉，發生錯誤：${error instanceof Error ? error.message : '未知錯誤'}`,
      timestamp: createTimestamp(),
    })
    persistConversationCache()
  }

  const setStructuredTaskOutput = (value: StructuredTaskOutput | null) => {
    structuredTaskOutput.value = value
  }

  const resetConversationSession = () => {
    clearConversationCache()
    conversationId.value = null
    structuredTaskOutput.value = null
    messages.value = getDefaultMessages()
    window.location.reload()
  }

  const sendMessage = async (): Promise<{ ok: true } | { ok: false }> => {
    if (!userInput.value.trim() || isLoading.value) {
      return { ok: false }
    }

    if (!conversationId.value) {
      console.error('Conversation ID is missing before sending a message.')
      return { ok: false }
    }

    const inputText = userInput.value.trim()
    userInput.value = ''

    messages.value.push({
      id: createMessageId(),
      type: 'user',
      content: inputText,
      timestamp: createTimestamp(),
    })
    persistConversationCache()

    isLoading.value = true
    progressStatusText.value = '準備送出需求...'
    let requestId = createRequestId()
    progressStream = startProgressStream(conversationId.value, requestId)

    try {
      let response

      try {
        response = await sendUserRequest(inputText, conversationId.value, requestId)
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          progressStream?.close()
          progressStream = null
          await rebuildConversation()
          requestId = createRequestId()
          progressStream = startProgressStream(conversationId.value!, requestId)
          messages.value.push({
            id: createMessageId(),
            type: 'user',
            content: inputText,
            timestamp: createTimestamp(),
          })
          persistConversationCache()
          response = await sendUserRequest(inputText, conversationId.value!, requestId)
        } else {
          throw error
        }
      }

      if (response.conversation_id) {
        conversationId.value = response.conversation_id
        saveConversationId(response.conversation_id)
      }

      messages.value.push({
        id: createMessageId(),
        type: 'ai',
        content: response.reply_text,
        timestamp: response.reply_created_at ?? createTimestamp(),
      })
      if (response.structured_task_output) {
        structuredTaskOutput.value = response.structured_task_output
      }
      persistConversationCache()
      return { ok: true }
    } catch (error) {
      appendErrorMessage(error)
      return { ok: false }
    } finally {
      progressStream?.close()
      progressStream = null
      isLoading.value = false
      progressStatusText.value = '處理中...'
    }
  }

  onMounted(async () => {
    await initializeConversation()
  })

  return {
    conversationId,
    isInitializing,
    isLoading,
    messages,
    progressStatusText,
    resetConversationSession,
    sendMessage,
    setStructuredTaskOutput,
    structuredTaskOutput,
    userInput,
  }
}
