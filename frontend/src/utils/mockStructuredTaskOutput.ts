import type { StructuredTaskOutput } from '../types/app'

export const mockStructuredTaskOutput: StructuredTaskOutput = {
  plan_summary:
    '先釐清作業需求，再完成核心實作與測試，最後預留時間檢查與整理交付內容。',
  main_tasks: [
    {
      title: '需求解析與規劃準備',
      description: '確認作業題目、交付內容與技術限制，避免後續重工。',
      estimated_time: '1-2h',
      order: 1,
      subtasks: [
        {
          title: '閱讀題目與評分標準',
          description: '整理必做功能、輸入輸出格式與提交要求。',
          priority: 'high',
          estimated_time: '30m',
          order: 1,
        },
        {
          title: '建立需求清單',
          description: '列出核心功能、加分項與必要測試情境。',
          priority: 'medium',
          estimated_time: '45m',
          order: 2,
        },
      ],
    },
    {
      title: '核心程式設計與實作',
      description: '完成主要類別、資料流與功能邏輯，建立可執行版本。',
      estimated_time: '4-6h',
      order: 2,
      subtasks: [
        {
          title: '設計類別與方法',
          description: '先決定資料結構、類別責任與主要方法介面。',
          priority: 'high',
          estimated_time: '1h',
          order: 1,
        },
        {
          title: '完成核心功能',
          description: '依需求逐步實作主要邏輯，先確保基本功能能運作。',
          priority: 'high',
          estimated_time: '3h',
          order: 2,
        },
        {
          title: '補齊例外處理',
          description: '處理輸入異常、邊界條件與錯誤訊息。',
          priority: 'medium',
          estimated_time: '1h',
          order: 3,
        },
      ],
    },
    {
      title: '測試與修正',
      description: '驗證功能完整性，找出 bug 並回頭調整細節。',
      estimated_time: '2-3h',
      order: 3,
      subtasks: [
        {
          title: '執行正常流程測試',
          description: '確認主要功能在一般情況下可正確執行。',
          priority: 'high',
          estimated_time: '45m',
          order: 1,
        },
        {
          title: '驗證邊界情境',
          description: '測試空值、錯誤輸入與特殊條件。',
          priority: 'medium',
          estimated_time: '45m',
          order: 2,
        },
        {
          title: '修正 bug 與整理輸出',
          description: '修正問題並檢查輸出格式與註解。',
          priority: 'high',
          estimated_time: '1h',
          order: 3,
        },
      ],
    },
    {
      title: '最終檢查與提交準備',
      description: '確認檔案完整、命名正確，並預留最後緩衝時間。',
      estimated_time: '30-45m',
      order: 4,
      subtasks: [
        {
          title: '檢查檔案與執行方式',
          description: '確認專案可順利執行，提交檔案完整。',
          priority: 'medium',
          estimated_time: '20m',
          order: 1,
        },
        {
          title: '整理說明與提交',
          description: '補上必要說明並完成最終提交。',
          priority: 'medium',
          estimated_time: '20m',
          order: 2,
        },
      ],
    },
  ],
}
