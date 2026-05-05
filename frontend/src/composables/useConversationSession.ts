import { onMounted, ref } from 'vue'
import {
  ApiError,
  createConversation,
  getConversationHistory,
  sendUserRequest,
} from '../services/api'
import type { Message } from '../types/app'
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

  const createMessageId = () =>
    messages.value.reduce((maxId, message) => Math.max(maxId, message.id), 0) + 1

  const persistConversationCache = () => {
    saveConversationCache(messages.value, conversationId.value)
  }

  const applyHistoryMessages = async (currentConversationId: string) => {
    const history = await getConversationHistory(currentConversationId)
    let nextMessageId = 1
    const historyMessages = history.turns.flatMap(turn =>
      turn.messages.map(msg => ({
        id: nextMessageId++,
        type: msg.type,
        content: msg.content,
      })),
    )

    messages.value = historyMessages.length > 0
      ? historyMessages
      : getDefaultMessages()

    saveConversationCache(messages.value, currentConversationId)
  }

  const rebuildConversation = async () => {
    clearConversationCache()
    conversationId.value = await createConversation()
    saveConversationId(conversationId.value)
    messages.value = getDefaultMessages()
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
    })
    persistConversationCache()
  }

  const sendMessage = async (): Promise<{ ok: true; inputText: string } | { ok: false }> => {
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
    })
    persistConversationCache()

    isLoading.value = true

    try {
      const response = await sendUserRequest(inputText, conversationId.value)
      if (response.conversation_id) {
        conversationId.value = response.conversation_id
        saveConversationId(response.conversation_id)
      }

      messages.value.push({
        id: createMessageId(),
        type: 'ai',
        content: response.reply_text,
      })
      persistConversationCache()
      return { ok: true, inputText }
    } catch (error) {
      appendErrorMessage(error)
      return { ok: false }
    } finally {
      isLoading.value = false
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
    sendMessage,
    userInput,
  }
}
