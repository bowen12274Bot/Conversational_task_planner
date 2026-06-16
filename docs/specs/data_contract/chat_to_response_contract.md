# Chat Module 到 Response Module 資料契約

更新日期時間：2026-06-16 00:00:00

本文件用於定義 `Chat Module` 完成規劃相關問答後，交給 `Response Module` 包裝成前端對話區文字時的資料內容。

---

## 所在流程階段

本契約對應流程階段：

- `F020` / `N20`
- `chat_to_response_return_and_persistence_store`

---

## 資料物件一：Chat 回答結果

### 定義

由 `Chat Module` 產生的結構化回答結果。此資料代表本輪使用者的問題已被回答，但不代表既有排程已被修改。

### 組成內容

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `answer_types` | list[string] | 是 | 回答類型，可疊加，例如 `execution_advice` 與 `resource_suggestion` |
| `answer` | string | 是 | Chat Module 產生的實質回答內容 |
| `referenced_plan` | object 或 null | 否 | 本回答引用的既有規劃位置 |
| `suggested_follow_up_actions` | list | 否 | 可供後續互動使用的建議動作，不代表本輪已執行 |

### `referenced_plan`

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `main_task_order` | number 或 null | 否 | 回答主要指向的主任務順序 |
| `subtask_orders` | list[string] | 否 | 回答涉及的子任務順序 |

### `suggested_follow_up_actions`

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `action_type` | string | 是 | 後續可選行為，例如 `revise_plan`、`ask_more` |
| `label` | string | 是 | 給使用者或前端使用的簡短文字 |

---

## 約束

- `Chat Module` 不得輸出新的完整排程
- `Chat Module` 不得輸出局部排程修改結果
- 此資料不得交給 `Output Structuring Module`
- 控制層不得因本資料更新 `structured_task_output`
- `suggested_follow_up_actions` 只能表示「可以接著做什麼」，不能視為已執行動作

---

## 範例

```json
{
  "answer_types": [
    "execution_advice",
    "resource_suggestion"
  ],
  "answer": "第三階段的模擬試題練習可以分成三個方向：先做限時完整模考，接著整理錯題類型，最後針對常錯題型回補練習。學習管道可優先使用官方範例題、模擬試題書與可計時的線上題庫。",
  "referenced_plan": {
    "main_task_order": 3,
    "subtask_orders": ["3.1", "3.2"]
  },
  "suggested_follow_up_actions": [
    {
      "action_type": "revise_plan",
      "label": "將練習方向加入第三階段"
    }
  ]
}
```
