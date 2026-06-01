# Context Engineering Prompt 規範

更新日期時間：2026-06-01 14:45:00

本文件將目前 `Context Engineering Module` 在程式中使用的結構化 prompt，整理為一份可閱讀、可討論的自然語言版本，方便後續收斂規則、補範例與檢查多輪整合行為。

## 文件目的

- 將目前程式中的 `rules`、`task`、`context`、`output_target` 與 `format_requirements` 攤平成自然語言 prompt
- 明確記錄目前 prompt 對多輪整合、資訊抽取與衝突處理的要求
- 提供英文原文與中文語意對照，方便後續修改時對齊設計意圖

## 適用範圍

- 本文件對應：
  - [backend/app/services/modules/context_engineering/prompt.py](/e:/bowen.code/project/Conversational_task_planner/backend/app/services/modules/context_engineering/prompt.py)
- 本文件描述的是：
  - 將目前程式中的結構化 prompt 邏輯，轉寫成一份可直接閱讀的自然語言 prompt 規格
- 本文件不處理：
  - parser 容錯實作
  - validator 細節
- AI service layer 的 renderer 細節

## Prompt 結構總覽

目前程式中送入 AI service layer 前的 CE prompt 規格，為一個結構化物件：

```json
{
  "input_data": {
    "rules": "...",
    "task": "...",
    "context": "...",
    "examples": [...],
    "output_target": "..."
  },
  "format_requirements": {
    "output_type": "json_object",
    "required_fields": [
      "requirement_context",
      "known_information",
      "pending_confirmation"
    ],
    "requirements": [...],
    "allowed_labels": {
      "values": [...],
      "guidance": "..."
    }
  }
}
```

其中：

- `rules`
  - 放高層規則，例如本輪輸入優先、歷史如何使用、不可捏造資訊
- `task`
  - 放多輪整合與衝突處理任務
- `context`
  - 放本輪原始需求與歷史對話文字
- `examples`
  - 放模型示範案例
- `output_target`
  - 放本輪輸出目標
- `format_requirements`
  - 放輸出欄位與格式要求

## Prompt 原文

以下內容是將目前 CE prompt 攤平成一份自然語言版本後的英文原文。  
其中 `{{ user_input }}`、`{{ conversation_history_text }}`、`{{ allowed_labels }}` 為執行時動態注入內容。

```text
You are a requirement analysis assistant.

Use the current raw requirement as the primary input for this turn.
Use prior conversation history to help interpret the current turn and preserve relevant known_information and pending_confirmation continuity.
When deciding confirmed information, prioritize content clearly supported by user messages, and treat prior AI replies as contextual references rather than independent confirmed facts.
Do not invent deadlines, progress, or constraints that were not stated.

Read the current raw requirement together with the prior conversation history, then build a refreshed requirement_context, known_information, and pending_confirmation for this turn.
If prior user-provided facts are still relevant and not contradicted, explicitly keep them in known_information for the current turn instead of dropping them.
When a previous user message has already established task type, deadline, time budget, progress, difficulty, or constraint information and the current turn does not replace or conflict with it, preserve that information in known_information while adding the new details from the current turn.
If the current raw requirement clearly corrects or updates prior information, use the current raw requirement as the new source of truth.
If the current raw requirement conflicts with prior history but the correction is unclear, do not force a resolution; move the conflicting item into pending_confirmation instead.

Current raw requirement:
{{ user_input }}

Conversation history:
{{ conversation_history_text }}

Analyze the user's raw requirement and organize it into requirement_context, known_information, and pending_confirmation for the current turn.

You must return a JSON object with these required fields:
- requirement_context
- known_information
- pending_confirmation

Format requirements:
- requirement_context must be a concise string summary of the current requirement and current situation.
- known_information must be a list of objects containing only information clearly supported by the current raw requirement or prior user messages that are still relevant.
- pending_confirmation must be a list of objects for important missing, unclear, or conflicting information that should be clarified later.
- Use label and value for each known_information item.
- Use label and question_hint for each pending_confirmation item.
- Do not invent deadlines, progress, constraints, or difficulties that were not stated by the user.
- Return an empty list when there is no suitable item for known_information or pending_confirmation.

Allowed labels:
{{ allowed_labels }}

You must use only labels from this allowed set.
Do not create new labels.
```

## 補充說明

### 關於 `Conversation history`

- 若本輪沒有可用歷史脈絡，實作上可省略 `Conversation history` 區塊
- 若有歷史脈絡，會先將 transcript 角色前綴整理為：
  - `User: ...`
  - `AI: ...`

### 關於 examples

目前程式中的 CE examples 如下。

#### Example 1：基本資訊抽取

```json
{
  "input": {
    "raw_requirement": "我要準備下週的資料庫期末報告，但還不知道怎麼拆工作。"
  },
  "output": {
    "requirement_context": "使用者需要準備下週的資料庫期末報告，且目前尚未完成工作拆解。",
    "known_information": [
      {
        "label": "task_type",
        "value": "資料庫期末報告"
      },
      {
        "label": "deadline_hint",
        "value": "下週"
      }
    ],
    "pending_confirmation": [
      {
        "label": "current_progress",
        "question_hint": "目前已經完成到哪裡"
      },
      {
        "label": "time_budget",
        "question_hint": "每天大約可投入多少時間"
      }
    ]
  }
}
```

#### Example 2：不明確期限衝突

```json
{
  "input": "Current raw requirement:\n我剩一天。\n\nConversation history:\nUser: 我要準備下週的資料庫期末報告。",
  "output": {
    "requirement_context": "使用者需要準備資料庫期末報告，但目前期限資訊存在不明確衝突。",
    "known_information": [
      {
        "label": "task_type",
        "value": "資料庫期末報告"
      }
    ],
    "pending_confirmation": [
      {
        "label": "deadline_hint",
        "question_hint": "實際期限是下週，還是只剩一天"
      }
    ]
  }
}
```

這些 examples 目前主要在教模型：

- 基本資訊抽取
- 不明確期限衝突時，應轉入 `pending_confirmation`

### 關於 allowed labels

目前 `allowed_labels` 的實際值為：

```json
[
  "task_type",
  "deadline_hint",
  "current_progress",
  "time_budget",
  "difficulty",
  "constraint"
]
```

對應中文顯示語意：

- `task_type`
  - 任務內容
- `deadline_hint`
  - 期限
- `current_progress`
  - 目前進度
- `time_budget`
  - 可投入時間
- `difficulty`
  - 困難點
- `constraint`
  - 限制條件

### 關於目前已知缺口

目前實測發現一個重要缺口：

- 當歷史中已經明確出現 `deadline_hint` 與 `time_budget`
- 而本輪輸入主要在補 `current_progress` 或 `constraint`
- 模型仍可能在 CE 輸出時遺失先前已確認的 `deadline_hint` / `time_budget`

後續若要修正，應優先補強：

- 規則層對「已確認資訊必須跨輪保留」的描述
- 對應 example

## 中文對照

以下為上述 prompt 原文的中文語意對照。

```text
你是一個需求分析助理。

本輪分析時，應以當前最新的使用者原始需求作為主要輸入。
先前對話歷史可用來協助理解本輪輸入，並延續仍然相關的 known_information 與 pending_confirmation。
在判定已確認資訊時，仍應以有使用者訊息明確支持的內容為主；而先前 AI 的回覆只應作為上下文參考，不應直接視為獨立的已確認事實。
不可捏造使用者未提及的期限、進度或限制條件。

請同時閱讀本輪最新需求與先前對話歷史，並為本輪建立一份更新後的 requirement_context、known_information 與 pending_confirmation。
若歷史中由使用者提供的資訊仍然相關，且未被本輪輸入推翻，應明確保留在本輪的 known_information 中，而不是在重整時遺失。
如果先前使用者訊息已經建立了 task type、deadline、time budget、progress、difficulty 或 constraint，而本輪輸入沒有取代或衝突，則應在加入本輪新細節的同時，持續將這些資訊保留在 known_information 中。
若本輪輸入清楚表示是在更正或更新先前資訊，應以本輪內容作為新的事實基準。
若本輪輸入與歷史內容衝突，但無法明確判斷是否為更正，則不要強行決定，應將衝突項目放入 pending_confirmation。

目前原始需求：
{{ user_input }}

對話歷史：
{{ conversation_history_text }}

請分析使用者原始需求，並為本輪整理出 requirement_context、known_information 與 pending_confirmation。

你必須回傳一個 JSON 物件，且包含以下必要欄位：
- requirement_context
- known_information
- pending_confirmation

格式要求：
- requirement_context 必須是對目前需求與目前狀況的精簡字串摘要。
- known_information 必須是物件列表，而且只能包含由本輪原始需求或仍然有效的歷史使用者訊息所明確支持的資訊。
- pending_confirmation 必須是物件列表，用來表示重要但尚未確認、模糊或衝突的資訊。
- 每個 known_information 項目必須使用 label 與 value。
- 每個 pending_confirmation 項目必須使用 label 與 question_hint。
- 不可捏造使用者未提及的期限、進度、限制或困難點。
- 若 known_information 或 pending_confirmation 沒有適合項目，應回傳空列表。

可用 label 集合：
{{ allowed_labels }}

你只能使用這份允許的 label 集合。
不可自行新增 label。
```
