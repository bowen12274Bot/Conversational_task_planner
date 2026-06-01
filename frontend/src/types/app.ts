export type Message = {
  id: number
  type: 'system' | 'user' | 'ai'
  content: string
}

export type StructuredSubtaskOutput = {
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  estimated_time: string
  order: number
}

export type StructuredMainTaskOutput = {
  title: string
  description: string
  estimated_time: string
  order: number
  subtasks: StructuredSubtaskOutput[]
}

export type StructuredTaskOutput = {
  plan_summary: string
  main_tasks: StructuredMainTaskOutput[]
}

export type ConversationCache = {
  messages: Message[]
  lastUpdated: string
}
