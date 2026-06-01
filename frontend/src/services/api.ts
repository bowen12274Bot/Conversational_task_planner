import type { StructuredTaskOutput } from '../types/app'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message?: string) {
    super(message ?? `HTTP ${status}`)
    this.name = 'ApiError'
    this.status = status
  }
}

type PingResponse = {
  message: string
}

type FrontendToControllerRequest = {
  user_input: string
  conversation_id: string
  interaction_info?: Record<string, any>
}

type ControllerToFrontendResponse = {
  reply_text: string
  reply_created_at?: string | null
  conversation_id?: string | null
  structured_task_output?: StructuredTaskOutput | null
}

type CreateConversationResponse = {
  conversation_id: string
}

type ConversationHistoryResponse = {
  conversation_id: string
  structured_task_output?: StructuredTaskOutput | null
  turns: Array<{
    turn_id: string
    messages: Array<{
      type: 'system' | 'user' | 'ai'
      content: string
      created_at: string
    }>
  }>
}

export async function getPingMessage(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/ping`)

  if (!response.ok) {
    throw new ApiError(response.status)
  }

  const data = (await response.json()) as PingResponse
  return data.message
}

export async function sendUserRequest(userInput: string, conversationId: string): Promise<ControllerToFrontendResponse> {
  const payload: FrontendToControllerRequest = {
    user_input: userInput,
    conversation_id: conversationId,
    interaction_info: {}
  }

  const response = await fetch(`${API_BASE_URL}/api/raw-request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    throw new ApiError(response.status)
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
    throw new ApiError(response.status)
  }

  const data = (await response.json()) as CreateConversationResponse
  return data.conversation_id
}

export async function getConversationHistory(conversationId: string): Promise<ConversationHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/history`)

  if (!response.ok) {
    throw new ApiError(response.status)
  }

  return (await response.json()) as ConversationHistoryResponse
}
