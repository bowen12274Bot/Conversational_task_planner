export type Message = {
  id: number
  type: 'system' | 'user' | 'ai'
  content: string
  timestamp?: string
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

export type StructuredSummaryMetricsOutput = {
  total_estimated_time_text: string
  daily_time_budget_text: string
  estimated_completion_text: string
}

export type StructuredTaskOutput = {
  plan_summary: string
  summary_metrics: StructuredSummaryMetricsOutput
  main_tasks: StructuredMainTaskOutput[]
}

export type ConversationCache = {
  messages: Message[]
  lastUpdated: string
}
