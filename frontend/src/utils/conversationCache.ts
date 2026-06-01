import type { ConversationCache, Message } from '../types/app'

let inMemoryConversationCache: ConversationCache | null = null
let inMemoryConversationId: string | null = null
const CONVERSATION_ID_KEY = 'conversation_id'

export const DEFAULT_WELCOME_MESSAGE: Message = {
  id: 1,
  type: 'system',
  content: '歡迎使用對話式任務規劃系統！請輸入您的作業或小專題目標。',
  timestamp: new Date().toISOString(),
}

export function getDefaultMessages(): Message[] {
  return [DEFAULT_WELCOME_MESSAGE]
}

export function saveConversationCache(
  messages: Message[],
  conversationId: string | null,
): void {
  inMemoryConversationCache = {
    messages,
    lastUpdated: new Date().toISOString(),
  }
  inMemoryConversationId = conversationId

  if (conversationId) {
    localStorage.setItem(CONVERSATION_ID_KEY, conversationId)
  }
}

export function loadConversationCache():
  | { conversationId: string; cache: ConversationCache }
  | null {
  const conversationId = inMemoryConversationId ?? localStorage.getItem(CONVERSATION_ID_KEY)

  if (!conversationId) {
    return null
  }

  inMemoryConversationId = conversationId

  if (!inMemoryConversationCache) {
    return {
      conversationId,
      cache: {
        messages: [],
        lastUpdated: '',
      },
    }
  }

  return {
    conversationId,
    cache: inMemoryConversationCache,
  }
}

export function saveConversationId(conversationId: string): void {
  inMemoryConversationId = conversationId
  localStorage.setItem(CONVERSATION_ID_KEY, conversationId)
}

export function loadConversationId(): string | null {
  const conversationId = inMemoryConversationId ?? localStorage.getItem(CONVERSATION_ID_KEY)

  if (!conversationId) {
    return null
  }

  inMemoryConversationId = conversationId
  return conversationId
}

export function clearConversationCache(): void {
  inMemoryConversationCache = null
  inMemoryConversationId = null
  localStorage.removeItem(CONVERSATION_ID_KEY)
}
