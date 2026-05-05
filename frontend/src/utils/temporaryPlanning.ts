import { ref } from 'vue'
import type { PlanTask, Subtask } from '../types/app'

export function useTemporaryPlanning() {
  const planTasks = ref<PlanTask[]>([])

  const addPlanTask = (userInput: string) => {
    planTasks.value.push(createPlanTask(userInput))
  }

  const toggleSubtaskCompletion = (planId: string, subtaskId: string) => {
    const plan = planTasks.value.find(item => item.id === planId)
    const subtask = plan?.subtasks.find(item => item.id === subtaskId)

    if (subtask) {
      subtask.completed = !subtask.completed
    }
  }

  return {
    addPlanTask,
    planTasks,
    toggleSubtaskCompletion,
  }
}

function createPlanTask(userInput: string): PlanTask {
  return {
    id: `plan-${Date.now()}`,
    title: deriveTitle(userInput),
    due: deriveDue(userInput),
    createdAt: new Date(),
    subtasks: createSubtasks(),
  }
}

function deriveTitle(userInput: string): string {
  const lower = userInput.toLowerCase()

  if (lower.includes('java') && lower.includes('作業')) {
    return 'Java作業'
  }

  if (lower.includes('作業')) {
    return '作業規劃'
  }

  if (lower.includes('專題')) {
    return '專題規劃'
  }

  return userInput
}

function deriveDue(userInput: string): string | undefined {
  const match = userInput.match(/(\d+\s*天(?:完成)?)/)
  return match ? match[1].replace(/\s+/g, '') : undefined
}

function createSubtasks(): Subtask[] {
  const baseId = Date.now()

  return [
    {
      id: `subtask-${baseId}-1`,
      title: '分析需求與規劃',
      description: '理解任務內容與預期成果',
      priority: 1,
      estimatedTime: '1小時',
      completed: false,
    },
    {
      id: `subtask-${baseId}-2`,
      title: '收集資料與研究',
      description: '蒐集相關參考資料與素材',
      priority: 2,
      estimatedTime: '2小時',
      completed: false,
    },
    {
      id: `subtask-${baseId}-3`,
      title: '執行與實作',
      description: '按照規劃執行任務內容',
      priority: 3,
      estimatedTime: '4小時',
      completed: false,
    },
    {
      id: `subtask-${baseId}-4`,
      title: '檢查與修改',
      description: '檢查成果並修正問題',
      priority: 4,
      estimatedTime: '1小時',
      completed: false,
    },
  ]
}
