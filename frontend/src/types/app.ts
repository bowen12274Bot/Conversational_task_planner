export type Message = {
  id: number
  type: 'system' | 'user' | 'ai'
  content: string
}

export type Subtask = {
  id: string
  title: string
  description?: string
  priority: number
  estimatedTime?: string
  completed: boolean
}

export type PlanTask = {
  id: string
  title: string
  due?: string
  createdAt: Date
  subtasks: Subtask[]
}

export type ConversationCache = {
  messages: Message[]
  lastUpdated: string
}
