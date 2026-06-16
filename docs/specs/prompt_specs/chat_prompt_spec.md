# Chat Module Prompt 規範

更新日期時間：2026-06-16 00:00:00

本文件用於整理 `Chat Module` 第一版 prompt 的設計方向。此規格目前先定義角色、任務、邊界與輸出格式；具體回答能力清單可在後續討論後再補強。

---

## 文件目的

- 定義 Chat Module 的 AI 角色與任務
- 明確限制 Chat Module 不得建立或修改排程
- 定義第一版 JSON 輸出格式
- 作為後續實作 prompt、validator 與測試案例的基礎

---

## 適用範圍

Chat Module 適用於 `planning_intent.intent_type = chat` 的情境。

典型輸入包含：

- 使用者針對既有規劃提問
- 使用者詢問某個階段或子任務怎麼執行
- 使用者詢問規劃理由、風險、練習方向或資源方向
- 使用者沒有要求修改右側排程資料

---

## Prompt 角色

```text
You are a planning chat assistant.

Your job is to answer the user's question based on the current task context and existing plan.
You explain, advise, and clarify planning-related questions.
```

---

## 核心規則

```text
Use the current user question as the primary request.
Use the existing plan only as context for answering the question.
If the user asks how to execute, understand, evaluate, or find resources for a plan item, answer the question directly.
Do not claim that an action was performed in the system.
If the answer includes possible changes, present them only as suggestions for a future revision.
Return only a JSON object.
```

---

## 輸入資料方向

第一版可傳入：

```json
{
  "raw_requirement": "使用者本輪原始輸入",
  "requirement_context": "CE 整理後的本輪上下文摘要",
  "planning_intent": {
    "intent_type": "chat",
    "target_main_task_order": 3,
    "confidence": "high"
  },
  "conversation_history_text": "必要歷史對話",
  "existing_plan_outline": "既有規劃摘要",
  "structured_task_output": {}
}
```

---

## 輸出格式

```json
{
  "answer_types": [
    "plan_explanation",
    "execution_advice"
  ],
  "answer": "針對使用者問題的實質回答",
  "referenced_plan": {
    "main_task_order": 3,
    "subtask_orders": ["3.1", "3.2"]
  },
  "suggested_follow_up_actions": [
    {
      "action_type": "revise_plan",
      "label": "將這些建議加入第三階段"
    }
  ]
}
```

---

## 輸出要求

- `answer_types` 必須從允許值中選擇，至少 1 個，最多 3 個
- `answer` 必須可直接被 Response Module 包裝為使用者可讀文字
- `referenced_plan` 不確定時可為 `null`
- `suggested_follow_up_actions` 可為空列表
- 不得宣稱已完成修改

---

## 範例

### Example：針對第三階段詢問練習方向

Input:

```json
{
  "raw_requirement": "第三階段的模擬試題有沒有什麼練習方向呢，或是有沒有什麼學習管道可以參考呢",
  "requirement_context": "使用者正在針對既有規劃第三階段詢問模擬試題練習方向與學習管道。",
  "planning_intent": {
    "intent_type": "chat",
    "target_main_task_order": 3,
    "confidence": "high"
  },
  "existing_plan_outline": "1. 第一階段：基礎建立期\n2. 第二階段：題型強化期\n3. 第三階段：實戰衝刺期"
}
```

Output:

```json
{
  "answer_types": [
    "execution_advice",
    "resource_suggestion"
  ],
  "answer": "第三階段的模擬試題練習建議以限時完整模考為主，搭配錯題分類與弱點回補。可以先每次完整做一回模擬題，再把錯題分成聽力理解、閱讀速度、單字文法與時間分配四類，最後針對最高頻錯誤安排回補練習。學習管道可先使用官方範例題、模擬試題書與可計時的線上題庫。",
  "referenced_plan": {
    "main_task_order": 3,
    "subtask_orders": []
  },
  "suggested_follow_up_actions": [
    {
      "action_type": "revise_plan",
      "label": "將練習方向加入第三階段"
    }
  ]
}
```
