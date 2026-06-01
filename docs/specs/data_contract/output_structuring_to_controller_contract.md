# Output Structuring 至控制層資料契約

本文件用於定義 `Output Structuring Module` 產出並回交控制層的排程顯示資料物件。

此資料契約的重點在於整理 `Planning Module` 已完成的規劃結果，使控制層能以穩定格式承接，並提供前端規劃面板直接渲染使用。

---

## 資料物件：Structured Task Output

### 定義

由 `Output Structuring Module` 根據 `PlanningCreateOutput` 整理出的前端排程顯示資料。

### 組成內容

- 規劃摘要
- 主任務集合

### 作用

- 作為控制層回傳前端規劃面板時使用的正式排程輸出資料
- 將 `Planning Module` 的規劃結果轉換為前端穩定可渲染的顯示格式
- 明確區分規劃說明層資料與排程顯示層資料

### 特性

- 此資料物件屬於顯示導向資料，不重新規劃任務內容
- `Structured Task Output` 的核心結構仍以 `main_tasks -> subtasks` 為基礎
- 現階段先支援主任務、子任務、排序與時間資訊顯示
- 現階段不處理時間軸、精確日期、依賴圖或前端互動狀態持久化

---

## 欄位定義

### `plan_summary`

- 型別：`string`
- 說明：提供前端規劃面板頂部顯示的整體規劃摘要

### `main_tasks`

- 型別：`list`
- 說明：由多筆主任務顯示資料組成的集合

### `main_tasks[].title`

- 型別：`string`
- 說明：主任務標題

### `main_tasks[].description`

- 型別：`string`
- 說明：主任務的簡短說明

### `main_tasks[].estimated_time`

- 型別：`string`
- 說明：主任務的預估投入時間

### `main_tasks[].order`

- 型別：`integer`
- 說明：主任務的顯示順序

### `main_tasks[].subtasks`

- 型別：`list`
- 說明：由多筆子任務顯示資料組成的集合

### `main_tasks[].subtasks[].title`

- 型別：`string`
- 說明：子任務標題

### `main_tasks[].subtasks[].description`

- 型別：`string`
- 說明：子任務的簡短說明

### `main_tasks[].subtasks[].priority`

- 型別：固定值集合
- 說明：子任務的相對優先程度

現階段建議值如下：

- `high`
- `medium`
- `low`

### `main_tasks[].subtasks[].estimated_time`

- 型別：`string`
- 說明：子任務的預估投入時間

### `main_tasks[].subtasks[].order`

- 型別：`integer`
- 說明：子任務在同一主任務底下的顯示順序

---

## 巢狀示範格式

```json
{
  "plan_summary": "先確認需求，再完成核心功能，最後安排測試與修正。",
  "main_tasks": [
    {
      "title": "確認作業需求與交付內容",
      "description": "整理題目要求、輸入輸出格式與評分重點。",
      "estimated_time": "1-2h",
      "order": 1,
      "subtasks": [
        {
          "title": "閱讀題目說明",
          "description": "確認題目要求與限制。",
          "priority": "high",
          "estimated_time": "30m",
          "order": 1
        },
        {
          "title": "列出必做功能",
          "description": "整理主要功能與交付範圍。",
          "priority": "high",
          "estimated_time": "30m",
          "order": 2
        }
      ]
    },
    {
      "title": "核心功能實作",
      "description": "完成主要程式功能。",
      "estimated_time": "4-6h",
      "order": 2,
      "subtasks": [
        {
          "title": "完成主要功能程式碼",
          "description": "依題目要求完成核心實作。",
          "priority": "high",
          "estimated_time": "3-4h",
          "order": 1
        }
      ]
    }
  ]
}
```

---

## 與其他資料契約的關係

- `PlanningCreateOutput` 定義於 [questioning_to_planning_create_contract.md](./questioning_to_planning_create_contract.md)
  - 負責表達 `Planning Module` 的完整建立結果
- `Structured Task Output` 定義於本文件
  - 負責表達前端規劃面板實際顯示所需的整理後資料
- `planning_schedule_structure_contract.md`
  - 定義 `Planning Module` 排程核心結構
  - `Structured Task Output` 以此結構為基礎，但補入前端直接顯示所需的 `plan_summary`

---

## 資料物件關係

| 階段 | 資料物件之間的關係                                 | 說明                                                                                     |
| ---- | -------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1    | Planning Create 輸出 -> Output Structuring 輸入    | `Output Structuring Module` 承接 `PlanningCreateOutput` 作為整理來源                     |
| 2    | Output Structuring 輸入 -> Structured Task Output  | 模組整理 `plan_summary` 與 `schedule.main_tasks`，產出前端可穩定渲染的排程顯示資料       |
| 3    | Structured Task Output -> 控制層 -> 前端規劃面板   | 控制層以本資料物件填入 `structured_task_output`，供前端主任務與子任務展開畫面直接顯示 |
