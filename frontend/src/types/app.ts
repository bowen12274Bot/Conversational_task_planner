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

export type ProgressEventType =
  | 'request_received'
  | 'context_engineering_started'
  | 'questioning_started'
  | 'route_decided'
  | 'planning_started'
  | 'revision_started'
  | 'chat_started'
  | 'response_started'
  | 'completed'
  | 'failed'

export type ProgressEvent = {
  conversation_id: string
  request_id: string
  event_type: ProgressEventType
  created_at: string
  turn_id?: string | null
  stage?: string | null
  route?: string | null
}
