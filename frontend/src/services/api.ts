const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

type PingResponse = {
  message: string
}

type FrontendToControllerRequest = {
  user_input: string
  interaction_info?: Record<string, any>
}

type ControllerToFrontendResponse = {
  reply_text: string
  structured_task_output?: Record<string, any> | null
}

type CreateConversationResponse = {
  conversation_id: string
}

type ConversationHistoryResponse = {
  messages: Array<{
    id: string
    type: 'system' | 'user' | 'ai'
    content: string
    timestamp: string
  }>
  plan_tasks?: Array<{
    id: string
    title: string
    due?: string
    created_at: string
    subtasks: Array<{
      id: string
      title: string
      description?: string
      priority: number
      estimated_time?: string
      completed: boolean
    }>
  }>
}

export async function getPingMessage(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/ping`)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const data = (await response.json()) as PingResponse
  return data.message
}

export async function sendUserRequest(userInput: string, conversationId?: string): Promise<ControllerToFrontendResponse> {
  const payload: FrontendToControllerRequest = {
    user_input: userInput,
    interaction_info: conversationId ? { conversation_id: conversationId } : {}
  }

  const response = await fetch(`${API_BASE_URL}/api/raw-request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return (await response.json()) as ControllerToFrontendResponse
}

export async function createConversation(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const data = (await response.json()) as CreateConversationResponse
  return data.conversation_id
}

export async function getConversationHistory(conversationId: string): Promise<ConversationHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/history`)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return (await response.json()) as ConversationHistoryResponse
}
